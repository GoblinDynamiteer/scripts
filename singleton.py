#!/usr/bin/env python3

class Singleton(type):
    instances = {}

    def __call__(class_type, *args, **kwargs):
        if class_type not in class_type.instances:
            class_type.instances[class_type] = super(
                Singleton, class_type).__call__(*args, **kwargs)
        return class_type.instances[class_type]