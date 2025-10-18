"""Unit tests for Loppers."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from loppers import extract_skeleton, find_files, get_skeleton
from loppers.loppers import SkeletonExtractor
from binaryornot.check import is_binary


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
        skeleton: str = extract_skeleton(code, "python")
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
        skeleton: str = extract_skeleton(code, "python")
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
            "kotlin",
            "swift",
            "lua",
            "scala",
            "groovy",
            "objc",
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
        skeleton: str = extract_skeleton(code, "javascript")
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
        skeleton: str = extract_skeleton(code, "java")
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
        skeleton: str = extract_skeleton(code, "python")
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
        skeleton: str = extract_skeleton(code, "java")
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
        skeleton: str = extract_skeleton(code, "csharp")
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
        skeleton: str = extract_skeleton(code, "rust")
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
        skeleton: str = extract_skeleton(code, "cpp")
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
        skeleton: str = extract_skeleton(code, "ruby")
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
        skeleton: str = extract_skeleton(code, "php")
        self.assertIn("public function process", skeleton)
        self.assertNotIn("return $item * 2", skeleton)

    def test_swift_functions_and_methods(self) -> None:
        """Test Swift function and method extraction."""
        code: str = '''
func greet(name: String) -> String {
    return "Hello, \\(name)!"
}

class Greeter {
    func sayHello() {
        print("Hello!")
    }

    func sayGoodbye(name: String) {
        print("Goodbye, \\(name)!")
    }
}
'''
        skeleton: str = extract_skeleton(code, "swift")
        self.assertIn("func greet(name: String) -> String", skeleton)
        self.assertIn("func sayHello()", skeleton)
        self.assertIn("func sayGoodbye(name: String)", skeleton)
        self.assertNotIn("print", skeleton)
        self.assertNotIn("return", skeleton)

    def test_lua_functions(self) -> None:
        """Test Lua function extraction."""
        code: str = '''
function greet(name)
    local greeting = "Hello " .. name
    print(greeting)
    return greeting
end

function sayGoodbye()
    print("Goodbye")
end
'''
        skeleton: str = extract_skeleton(code, "lua")
        self.assertIn("function greet(name)", skeleton)
        self.assertIn("function sayGoodbye()", skeleton)
        self.assertNotIn("local greeting", skeleton)
        self.assertNotIn("print", skeleton)

    def test_scala_functions_and_methods(self) -> None:
        """Test Scala function and method extraction."""
        code: str = '''
def greet(name: String): String = {
    val greeting = "Hello " + name
    println(greeting)
    greeting
}

class Greeter {
    def sayHello(): Unit = {
        println("Hello!")
    }
}
'''
        skeleton: str = extract_skeleton(code, "scala")
        self.assertIn("def greet(name: String): String =", skeleton)
        self.assertIn("def sayHello(): Unit =", skeleton)
        self.assertNotIn("val greeting", skeleton)
        self.assertNotIn("println", skeleton)

    def test_groovy_functions(self) -> None:
        """Test Groovy function extraction."""
        code: str = '''
def greet(name) {
    def greeting = "Hello " + name
    println(greeting)
    return greeting
}

class Greeter {
    def sayHello() {
        println("Hello!")
    }
}
'''
        skeleton: str = extract_skeleton(code, "groovy")
        self.assertIn("def greet(name)", skeleton)
        self.assertIn("def sayHello()", skeleton)
        self.assertNotIn("def greeting", skeleton)
        self.assertNotIn("println", skeleton)

    def test_objective_c_methods(self) -> None:
        """Test Objective-C method extraction."""
        code: str = '''
- (NSString *)greet:(NSString *)name {
    NSString *greeting = @"Hello";
    NSLog(@"%@", greeting);
    return greeting;
}

- (void)printMessage {
    NSLog(@"Message");
}
'''
        skeleton: str = extract_skeleton(code, "objc")
        self.assertIn("- (NSString *)greet:(NSString *)name", skeleton)
        self.assertIn("- (void)printMessage", skeleton)
        self.assertNotIn("NSString *greeting", skeleton)
        self.assertNotIn("NSLog", skeleton)

    def test_kotlin_functions_and_properties(self) -> None:
        """Test Kotlin function and property extraction."""
        code: str = '''
fun greet(name: String): String {
    return "Hello, $name"
}

class User {
    private var _age: Int = 0

    var age: Int
        get() {
            return _age
        }
        set(value) {
            _age = value
        }

    fun validate() {
        if (_age < 0) throw IllegalArgumentException("Invalid age")
    }

    fun getName(): String {
        return "User"
    }
}
'''
        skeleton: str = extract_skeleton(code, "kotlin")
        self.assertIn("fun greet(name: String): String", skeleton)
        self.assertIn("fun validate()", skeleton)
        self.assertIn("fun getName(): String", skeleton)
        self.assertIn("var age: Int", skeleton)
        self.assertNotIn('return "Hello, $name"', skeleton)
        self.assertNotIn("throw IllegalArgumentException", skeleton)


class TestBinaryFileDetection(unittest.TestCase):
    """Test binary file detection."""

    def test_text_file_not_binary(self) -> None:
        """Test that text files are not detected as binary."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Hello, this is a text file\n")
            f.flush()
            path = Path(f.name)
            try:
                self.assertFalse(is_binary(str(path)))
            finally:
                path.unlink()

    def test_binary_extension_detected(self) -> None:
        """Test that files with known binary extensions are detected."""
        # binaryornot detects based on known extensions and null bytes
        # Test with a known binary extension + null byte content
        with tempfile.NamedTemporaryFile(suffix=".pyc", delete=False, mode="wb") as f:
            f.write(b"Python compiled\x00binary\x00content")
            f.flush()
            path = Path(f.name)
            try:
                self.assertTrue(is_binary(str(path)))
            finally:
                path.unlink()

    def test_null_byte_detection(self) -> None:
        """Test that files with null bytes are detected as binary."""
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".txt", delete=False) as f:
            # Files with null bytes fail UTF-8 decoding
            f.write(b"Some text\x00with null bytes")
            f.flush()
            path = Path(f.name)
            try:
                self.assertTrue(is_binary(str(path)))
            finally:
                path.unlink()

    def test_python_file_not_binary(self) -> None:
        """Test that Python files are not detected as binary."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("def hello():\n    print('hello')\n")
            f.flush()
            path = Path(f.name)
            try:
                self.assertFalse(is_binary(str(path)))
            finally:
                path.unlink()

    def test_empty_file_not_binary(self) -> None:
        """Test that empty files are not detected as binary."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.flush()
            path = Path(f.name)
            try:
                self.assertFalse(is_binary(str(path)))
            finally:
                path.unlink()

    def test_image_extension_detected(self) -> None:
        """Test that binary image files with null bytes are detected."""
        # binaryornot detects binary content via null bytes
        test_cases = [
            (".jpg", b"\xFF\xD8\xFF\xE0\x00image"),  # JPEG with null byte
            (".png", b"\x89PNG\r\n\x1a\n\x00data"),  # PNG with null byte
            (".gif", b"GIF89a\x00binary"),  # GIF with null byte
        ]
        for ext, content in test_cases:
            with tempfile.NamedTemporaryFile(suffix=ext, delete=False, mode="wb") as f:
                f.write(content)
                f.flush()
                path = Path(f.name)
                try:
                    self.assertTrue(is_binary(str(path)), f"{ext} should be detected as binary")
                finally:
                    path.unlink()


class TestFindFilesWithMixedTypes(unittest.TestCase):
    """Test find_files returns all non-binary text files."""

    def test_find_files_includes_non_code_files(self) -> None:
        """Test that find_files includes markdown, json, yaml, etc."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Create various file types
            (tmppath / "readme.md").write_text("# Test\n")
            (tmppath / "config.json").write_text('{"key": "value"}\n')
            (tmppath / "data.yaml").write_text("key: value\n")
            (tmppath / "script.py").write_text("def hello():\n    pass\n")

            # Find files
            files = find_files([tmppath], recursive=False)
            file_names = {f.name for f in files}

            # All text files should be included
            self.assertIn("readme.md", file_names)
            self.assertIn("config.json", file_names)
            self.assertIn("data.yaml", file_names)
            self.assertIn("script.py", file_names)

    def test_find_files_excludes_binary_files(self) -> None:
        """Test that find_files excludes binary files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Create text and binary files
            (tmppath / "text.txt").write_text("text content\n")
            (tmppath / "binary.bin").write_bytes(b"\x00\x01\x02\x03")

            files = find_files([tmppath], recursive=False)
            file_names = {f.name for f in files}

            self.assertIn("text.txt", file_names)
            self.assertNotIn("binary.bin", file_names)


class TestMixedFileTypes(unittest.TestCase):
    """Test mixed file type handling."""

    def test_get_skeleton_on_unsupported_file_as_is(self) -> None:
        """Test that unsupported files can't be extracted without language."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write('{"key": "value"}\n')
            f.flush()
            path = Path(f.name)

            try:
                # Should raise ValueError for unsupported file type
                with self.assertRaises(ValueError):
                    get_skeleton(path)
            finally:
                path.unlink()


class TestExtractWithUnsupportedFiles(unittest.TestCase):
    """Test extract command behavior with unsupported files."""

    def test_extract_requires_language_for_unsupported(self) -> None:
        """Test that extract requires -l for unsupported file types."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# Test\n")
            f.flush()
            path = Path(f.name)

            try:
                # Should raise ValueError for unsupported file type
                with self.assertRaises(ValueError):
                    get_skeleton(path)
            finally:
                path.unlink()

    def test_extract_with_explicit_language(self) -> None:
        """Test that extract works with explicit language for any file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("def hello():\n    print('hi')\n")
            f.flush()
            path = Path(f.name)

            try:
                # With explicit language, should work
                skeleton = extract_skeleton(path.read_text(), "python")
                self.assertIn("def hello()", skeleton)
                self.assertNotIn("print('hi')", skeleton)
            finally:
                path.unlink()


class TestIgnorePatternsWithMixedFiles(unittest.TestCase):
    """Test ignore patterns work correctly with all file types."""

    def test_default_ignore_patterns_apply(self) -> None:
        """Test that default ignore patterns apply to all file types."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Create node_modules with various files
            node_modules = tmppath / "node_modules"
            node_modules.mkdir()
            (node_modules / "package.json").write_text("{}\n")
            (node_modules / "module.js").write_text("module.exports = {};\n")

            # Create regular files
            (tmppath / "main.js").write_text("console.log('hi');\n")

            files = find_files(
                [tmppath],
                recursive=True,
                use_default_ignore=True,
            )
            file_names = {f.name for f in files}

            # Files in node_modules should be excluded
            self.assertIn("main.js", file_names)
            self.assertNotIn("package.json", file_names)
            self.assertNotIn("module.js", file_names)


if __name__ == "__main__":
    unittest.main()
