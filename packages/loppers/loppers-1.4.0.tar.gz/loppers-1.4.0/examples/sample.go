package main

import "fmt"

type Reader interface {
    Read(p []byte) (n int, err error)
    Close() error
}

type Writer interface {
    Write(p []byte) (n int, err error)
}

func fibonacci(n int) int {
    if n <= 1 {
        return n
    }
    return fibonacci(n-1) + fibonacci(n-2)
}

type Calculator struct {
    value int
}

type FileHandler struct {
    name string
}

func (c Calculator) Add(x, y int) int {
    return x + y
}

func (c Calculator) Multiply(x, y int) int {
    return x * y
}

func (f FileHandler) Read(p []byte) (n int, err error) {
    fmt.Println("Reading file:", f.name)
    return 0, nil
}

func (f FileHandler) Close() error {
    fmt.Println("Closing file:", f.name)
    return nil
}

func main() {
    callback := func(x int) int {
        return x * 2
    }
    result := callback(5)
}
