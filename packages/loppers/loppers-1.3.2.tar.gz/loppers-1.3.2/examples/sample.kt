/**
 * Kotlin sample file demonstrating various language constructs.
 */

// Top-level function
fun calculateSum(a: Int, b: Int): Int {
    val result = a + b
    println("Sum: $result")
    return result
}

// Extension function
fun String.isLongerThan(length: Int): Boolean {
    return this.length > length
}

// Data class
data class Person(
    val name: String,
    val age: Int
) {
    // Custom getter
    val isAdult: Boolean
        get() = age >= 18

    // Custom getter and setter
    var description: String = ""
        get() = "Person: $name"
        set(value) {
            println("Setting description to: $value")
            field = value
        }

    // Member function
    fun introduce() {
        println("Hello, I am $name and I am $age years old")
    }

    // Companion object
    companion object {
        fun create(name: String, birthYear: Int): Person {
            val age = 2024 - birthYear
            return Person(name, age)
        }
    }
}

// Sealed class
sealed class Result<T> {
    data class Success<T>(val data: T) : Result<T>()
    data class Error<T>(val exception: Exception) : Result<T>()

    fun getOrNull(): T? {
        return when (this) {
            is Success -> data
            is Error -> null
        }
    }
}

// Interface
interface Logger {
    fun log(message: String) {
        println("[LOG] $message")
    }

    fun error(message: String) {
        println("[ERROR] $message")
    }
}

// Class implementing interface
class ConsoleLogger : Logger {
    override fun log(message: String) {
        println("Console: $message")
    }
}

// Higher-order function
fun <T> applyFilter(items: List<T>, predicate: (T) -> Boolean): List<T> {
    val result = mutableListOf<T>()
    for (item in items) {
        if (predicate(item)) {
            result.add(item)
        }
    }
    return result
}

// Lambda with receiver
fun String.processWithLambda(transform: String.(String) -> String): String {
    return this.transform("processed")
}

// Scope function example
fun exampleScopeFunction() {
    val person = Person("Alice", 30).apply {
        introduce()
        description = "Experienced developer"
    }

    person.takeIf { it.isAdult }?.apply {
        println("Adult person: $name")
    }
}

// Main function
fun main() {
    val sum = calculateSum(5, 3)
    println("Result: $sum")

    val person = Person.create("Bob", 1990)
    person.introduce()

    val numbers = listOf(1, 2, 3, 4, 5)
    val filtered = applyFilter(numbers) { it > 2 }
    println("Filtered: $filtered")

    exampleScopeFunction()

    val logger: Logger = ConsoleLogger()
    logger.log("Application started")
}
