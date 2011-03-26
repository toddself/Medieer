#!/bin/bash
find . -name "*py" -print | xargs grep -hi "todo"
