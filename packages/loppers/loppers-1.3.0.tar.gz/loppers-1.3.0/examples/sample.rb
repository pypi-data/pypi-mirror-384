module Arithmetic
    def add(a, b)
        a + b
    end

    def subtract(a, b)
        a - b
    end
end

class Calculator
    include Arithmetic

    def multiply(a, b)
        result = a * b
        result
    end

    def self.divide(a, b)
        a / b
    end

    def process_items
        [1, 2, 3].each do |item|
            puts item * 2
        end
    end

    def validate
        true
    end
end

class AdvancedCalculator < Calculator
    def power(a, b)
        a ** b
    end

    def sqrt(n)
        Math.sqrt(n)
    end
end
