fn fibonacci(n: u32) -> u32 {
    if n <= 1 {
        return n;
    }
    fibonacci(n - 1) + fibonacci(n - 2)
}

pub struct Calculator {
    value: i32,
}

pub trait Arithmetic {
    fn add(&self, x: i32) -> i32;
    fn multiply(&self, x: i32) -> i32;
}

impl Calculator {
    pub fn new(initial: i32) -> Self {
        Calculator { value: initial }
    }

    pub fn add(&self, x: i32, y: i32) -> i32 {
        x + y
    }

    fn process(&self) {
        let closure = |x| x * 2;
        let result = closure(5);
    }
}

impl Arithmetic for Calculator {
    fn add(&self, x: i32) -> i32 {
        self.value + x
    }

    fn multiply(&self, x: i32) -> i32 {
        self.value * x
    }
}
