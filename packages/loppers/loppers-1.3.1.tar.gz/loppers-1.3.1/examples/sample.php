<?php

interface DataProcessor {
    public function process($data);
    public function validate($item);
}

trait LoggableTrait {
    public function log($message) {
        echo "LOG: " . $message;
    }

    protected function error($message) {
        echo "ERROR: " . $message;
    }
}

class Service implements DataProcessor {
    use LoggableTrait;

    public function process($data) {
        $callback = function($item) {
            return $item * 2;
        };

        $arrow = fn($x) => $x + 1;

        return array_map($callback, $data);
    }

    public function filter($items) {
        return array_filter($items, fn($x) => $x > 0);
    }

    public function validate($item) {
        return !empty($item);
    }
}

class AdvancedService extends Service {
    public function transform($data) {
        return array_map(function($item) {
            return $this->process($item);
        }, $data);
    }
}
?>
