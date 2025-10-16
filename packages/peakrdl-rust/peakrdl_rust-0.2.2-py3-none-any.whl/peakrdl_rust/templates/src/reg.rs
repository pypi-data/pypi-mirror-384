//! Register abstraction used to read, write, and modify register values

use core::marker::PhantomData;
use num_traits::{identities::ConstZero, AsPrimitive, Bounded, PrimInt};

pub trait Register: Copy {
    // NOTE: SystemRDL guarantees accesswidth <= regwidth, and both are 2^N bits where N >= 3
    type Regwidth: PrimInt + AsPrimitive<Self::Accesswidth> + ConstZero + 'static;
    type Accesswidth: PrimInt + AsPrimitive<Self::Regwidth>;

    unsafe fn from_raw(val: Self::Regwidth) -> Self;
    fn to_raw(self) -> Self::Regwidth;

    unsafe fn read_register(ptr: *const Self::Regwidth) -> Self {
        // this cast is OK since SystemRDL guarantees accesswidth <= regwidth,
        // and we won't access outside the bounds of the original pointer
        let ptr = ptr as *const Self::Accesswidth;
        let accesswidth = 8 * core::mem::size_of::<Self::Accesswidth>();
        let regwidth = 8 * core::mem::size_of::<Self::Regwidth>();
        let num_subwords = regwidth / accesswidth;
        // read one subword at a time, starting at the lowest address
        let mut result = Self::Regwidth::ZERO;
        for i in 0..num_subwords {
            let raw_val = Self::Accesswidth::from_{{ctx.endianness}}(unsafe { ptr.add(i).read_volatile() });
            result = result | raw_val.as_() << ((num_subwords - 1 - i) * accesswidth);
        }
        unsafe { Self::from_raw(result) }
    }

    unsafe fn write_register(ptr: *mut Self::Regwidth, value: Self) {
        // this is OK since SystemRDL guarantees accesswidth <= regwidth,
        // and we won't write outside the bounds of the original pointer
        let ptr = ptr as *mut Self::Accesswidth;
        let raw_value = value.to_raw();
        let accesswidth = 8 * core::mem::size_of::<Self::Accesswidth>();
        let regwidth = 8 * core::mem::size_of::<Self::Regwidth>();
        let mask = Self::Accesswidth::max_value().as_();
        let num_subwords = regwidth / accesswidth;
        // write one subword at a time, starting at the lowest address
        for i in 0..num_subwords {
            let subword = (raw_value >> ((num_subwords - 1 - i) * accesswidth)) & mask;
            unsafe {
                ptr.add(i).write_volatile(subword.as_().to_{{ctx.endianness}}());
            }
        }
    }
}

/// Read-write register access token
#[derive(Copy, Clone, PartialEq, Eq)]
pub struct RW;

/// Read-only register access token
#[derive(Copy, Clone, PartialEq, Eq)]
pub struct R;

/// Write-only register access token
#[derive(Copy, Clone, PartialEq, Eq)]
pub struct W;

mod sealed {
    use super::*;
    pub trait Access {}
    impl Access for R {}
    impl Access for W {}
    impl Access for RW {}
}

pub trait Access: sealed::Access + Copy {}

impl Access for R {}
impl Access for W {}
impl Access for RW {}

pub trait Read: Access {}
impl Read for RW {}
impl Read for R {}

pub trait Write: Access {}
impl Write for RW {}
impl Write for W {}

/// Register abstraction used to read, write, and modify register values
#[derive(Copy, Clone, PartialEq, Eq)]
pub struct Reg<T: Register, A: Access> {
    ptr: *mut T::Regwidth,
    phantom: PhantomData<A>,
}

unsafe impl<T: Register, A: Access> Send for Reg<T, A> {}
unsafe impl<T: Register, A: Access> Sync for Reg<T, A> {}

// pointer conversion functions
impl<T: Register, A: Access> Reg<T, A> {
    #[inline(always)]
    pub const unsafe fn from_ptr(ptr: *mut T::Regwidth) -> Self {
        Self {
            ptr,
            phantom: PhantomData,
        }
    }

    #[inline(always)]
    pub const fn as_ptr(&self) -> *mut T {
        self.ptr as _
    }
}

// read access
impl<T: Register, A: Read> Reg<T, A> {
    /// Read a register value.
    ///
    /// If the register is to be modified (i.e., a read-modify-write), use the
    /// [`Reg::modify`] method instead.
    ///
    /// # Example
    ///
    /// ```ignore
    /// let reg1_val = registers.regfile().register1().read();
    /// let field1_val = reg1_val.field1();
    /// let field2_val = reg1_val.field2();
    /// ```
    #[inline(always)]
    pub fn read(&self) -> T {
        unsafe { T::read_register(self.ptr) }
    }
}

// write access
impl<T: Register, A: Write> Reg<T, A> {
    /// Write a register value.
    ///
    /// Typically one would use [`Reg::write`] or [`Reg::modify`] to update a
    /// register's contents, but this method has a few different use cases such
    /// as updating a register with a stored value, or updating one register with
    /// the contents of another.
    ///
    /// # Example
    ///
    /// ```ignore
    /// let reg0 = registers.regfile().reg_array()[0].read();
    /// registers.regfile().reg_array()[1].write_value(reg0);
    /// ```
    #[inline(always)]
    pub fn write_value(&self, val: T) {
        unsafe { T::write_register(self.ptr, val) }
    }
}

impl<T: Default + Register, A: Write> Reg<T, A> {
    /// Write a register.
    ///
    /// This method takes a closure. The input to the closure is a mutable reference
    /// to the default value of the register. It can be updated in the closure. The
    /// updated value is then written to the hardware register.
    ///
    /// # Example
    ///
    /// ```ignore
    /// registers.regfile().register1().write(|r| {
    ///     // r contains the default (reset) value of the register
    ///     r.set_field1(0x1);
    ///     r.set_field2(0x0);
    /// });
    /// ```
    #[inline(always)]
    pub fn write<R>(&self, f: impl FnOnce(&mut T) -> R) -> R {
        let mut val = Default::default();
        let res = f(&mut val);
        self.write_value(val);
        res
    }
}

// read/write access
impl<T: Register, A: Read + Write> Reg<T, A> {
    /// Modify a register.
    ///
    /// This method takes a closure. The input to the closure is a mutable reference
    /// to the current value of the register. It can be updated in the closure. The
    /// updated value is then written back to the hardware register.
    ///
    /// # Example
    ///
    /// ```ignore
    /// let orig_r = registers.regfile().register1().modify(|r| {
    ///     // r contains the current value of the register
    ///     orig_r = r.clone()
    ///     r.set_field1(r.field1());
    ///     r.set_field2(0x0);
    ///     // whatever value the closure returns is returned by the .modify() method
    ///     orig r
    /// });
    /// ```
    #[inline(always)]
    pub fn modify<R>(&self, f: impl FnOnce(&mut T) -> R) -> R {
        let mut val = self.read();
        let res = f(&mut val);
        self.write_value(val);
        res
    }
}
