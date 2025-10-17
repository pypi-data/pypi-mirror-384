"""Unit tests for Loppers."""

from __future__ import annotations

import unittest

from loppers import extract, SkeletonExtractor


class TestSkeletonExtractor(unittest.TestCase):
    """Test skeleton extraction."""

    def test_python_extraction(self) -> None:
        """Test Python skeleton extraction."""
        code: str = '''
def hello(name):
    """Greet someone."""
    print(f"Hello {name}")
    return True
'''
        skeleton: str = extract(code, "python")
        self.assertIn("def hello", skeleton)
        self.assertIn("Greet someone", skeleton)
        self.assertNotIn("print", skeleton)

    def test_python_multiline_function(self) -> None:
        """Test multi-line Python function."""
        code: str = '''
def process(
    items: list,
    verbose: bool = False
) -> dict:
    result = {}
    for item in items:
        result[item] = process_item(item)
    return result
'''
        skeleton: str = extract(code, "python")
        self.assertIn("def process", skeleton)
        self.assertNotIn("result = {}", skeleton)

    def test_language_not_supported(self) -> None:
        """Test unsupported language error."""
        with self.assertRaises(ValueError):
            SkeletonExtractor("cobol")

    def test_supported_languages(self) -> None:
        """Test all supported languages can initialize."""
        languages: list[str] = [
            "python",
            "javascript",
            "typescript",
            "java",
            "go",
            "rust",
            "cpp",
            "c",
            "csharp",
            "ruby",
            "php",
        ]
        for lang in languages:
            try:
                extractor: SkeletonExtractor = SkeletonExtractor(lang)
                self.assertIsNotNone(extractor)
            except ImportError:
                # Skip if language not installed
                pass

    def test_javascript_arrow_functions(self) -> None:
        """Test JavaScript arrow function extraction."""
        code: str = '''
const add = (a, b) => {
    const result = a + b;
    return result;
};

const greet = (name) => {
    console.log(`Hello ${name}`);
    return true;
};

const concise = (x) => x * 2;
'''
        skeleton: str = extract(code, "javascript")
        self.assertIn("const add = (a, b) =>", skeleton)
        self.assertIn("const greet = (name) =>", skeleton)
        self.assertNotIn("const result", skeleton)
        self.assertNotIn("console.log", skeleton)

    def test_java_constructor(self) -> None:
        """Test Java constructor extraction."""
        code: str = '''
public class User {
    private String name;
    
    public User(String name) {
        this.name = name;
        this.validate();
    }
    
    private void validate() {
        if (name == null) throw new Exception("Invalid");
    }
}
'''
        skeleton: str = extract(code, "java")
        self.assertIn("public User(String name)", skeleton)
        self.assertIn("private void validate()", skeleton)
        self.assertNotIn("this.name = name", skeleton)
        self.assertNotIn("throw new Exception", skeleton)

    def test_python_with_underscore_methods(self) -> None:
        """Test Python __init__ and other dunder methods."""
        code: str = '''
class MyClass:
    def __init__(self, value):
        """Initialize."""
        self.value = value
        self._setup()
    
    def __str__(self):
        """String representation."""
        return f"MyClass({self.value})"
    
    def _setup(self):
        """Private setup method."""
        self.ready = True
'''
        skeleton: str = extract(code, "python")
        self.assertIn("def __init__", skeleton)
        self.assertIn('"""Initialize."""', skeleton)
        self.assertIn("def __str__", skeleton)
        self.assertIn('"""String representation."""', skeleton)
        self.assertIn("def _setup", skeleton)
        self.assertNotIn("self.value = value", skeleton)
        self.assertNotIn("self.ready = True", skeleton)

    def test_java_lambda(self) -> None:
        """Test Java lambda expressions."""
        code: str = '''
public class Example {
    public void test() {
        Function<Integer, Integer> doubler = x -> x * 2;
        Runnable r = () -> System.out.println("Hello");
    }
}
'''
        skeleton: str = extract(code, "java")
        self.assertIn("public void test()", skeleton)
        self.assertNotIn("System.out.println", skeleton)

    def test_csharp_properties_and_lambdas(self) -> None:
        """Test C# properties and lambda expressions."""
        code: str = '''
public class User {
    public string Name { get; set; }
    
    public int Age { 
        get { return _age; }
        set { _age = value; }
    }
    
    public void Process() {
        var result = items.Where(x => x.Value > 10);
        var anon = delegate(int x) { return x * 2; };
    }
}
'''
        skeleton: str = extract(code, "csharp")
        self.assertIn("public void Process()", skeleton)
        self.assertNotIn("return x * 2", skeleton)

    def test_rust_closures(self) -> None:
        """Test Rust closures."""
        code: str = '''
fn main() {
    let add = |a, b| a + b;
    let result = add(5, 3);
    
    let expensive_closure = |num| {
        let expensive_result = num * num;
        expensive_result + 1
    };
}
'''
        skeleton: str = extract(code, "rust")
        self.assertIn("fn main()", skeleton)
        # Closures should have bodies removed

    def test_cpp_lambdas(self) -> None:
        """Test C++ lambda expressions."""
        code: str = '''
void process() {
    auto add = [](int a, int b) { return a + b; };
    
    std::vector<int> v = {1, 2, 3};
    std::sort(v.begin(), v.end(), 
        [](int a, int b) { return a > b; });
}
'''
        skeleton: str = extract(code, "cpp")
        self.assertIn("void process()", skeleton)

    def test_ruby_methods_and_blocks(self) -> None:
        """Test Ruby methods and blocks."""
        code: str = '''
class Calculator
  def add(a, b)
    result = a + b
    result
  end
  
  def self.multiply(a, b)
    a * b
  end
  
  def process
    [1, 2, 3].each do |x|
      puts x * 2
    end
  end
end
'''
        skeleton: str = extract(code, "ruby")
        self.assertIn("def add", skeleton)
        self.assertIn("def self.multiply", skeleton)
        self.assertNotIn("result = a + b", skeleton)

    def test_php_anonymous_functions(self) -> None:
        """Test PHP anonymous and arrow functions."""
        code: str = '''
<?php
class Service {
    public function process($data) {
        $callback = function($item) {
            return $item * 2;
        };
        
        $arrow = fn($x) => $x + 1;
        
        return array_map($callback, $data);
    }
}
'''
        skeleton: str = extract(code, "php")
        self.assertIn("public function process", skeleton)
        self.assertNotIn("return $item * 2", skeleton)


if __name__ == "__main__":
    unittest.main()
