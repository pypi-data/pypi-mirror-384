#include <iostream>
#include <vector>
#include <algorithm>

void process() {
    auto add = [](int a, int b) { return a + b; };

    std::vector<int> v = {3, 1, 4, 1, 5, 9};
    std::sort(v.begin(), v.end(),
        [](int a, int b) { return a > b; });
}

class Calculator {
    int add(int x, int y) {
        return x + y;
    }

    ~Calculator() {
        cleanup();
    }
};
