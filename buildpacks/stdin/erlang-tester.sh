#!/bin/bash

run_test() {
  echo "test case: $1"
  /usr/bin/time -v bash -c "echo $1 | escript \"$ENTRY_FILE\" >> \"$OUTPUT_FOLDER/$RESULT_FILE\" 2>> \"$OUTPUT_FOLDER/$ERROR_FILE\""
}

TEST_CASES=(
    'Classic'
    'Classic,-strawberry'
    'Just Desserts'
    'Just Desserts,-ice cream,-peanut'
    'Just Desserts,-ice cream,-peanut,+peach'
    'Vegan Delite,+ice cream,-ice'
    'Greenie,-apple juice'
    'Freezie,+apple juice'
    "Forest Berry"
)

OUTPUT_FOLDER="/output"
RESULT_FILE="result"
ERROR_FILE="error"
MEMORY_FILE="memory"
ELAPSED_TIME_FILE="time"
MAX_MEMORY_USAGE="-1"
MAX_ELAPSED_TIME="-1"

touch "$OUTPUT_FOLDER/$RESULT_FILE"
cat /dev/null > "$OUTPUT_FOLDER/$RESULT_FILE"
touch "$OUTPUT_FOLDER/$ERROR_FILE"
cat /dev/null > "$OUTPUT_FOLDER/$ERROR_FILE"
touch "$OUTPUT_FOLDER/$MEMORY_FILE"
cat /dev/null > "$OUTPUT_FOLDER/$MEMORY_FILE"
touch "$OUTPUT_FOLDER/$ELAPSED_TIME_FILE"
cat /dev/null > "$OUTPUT_FOLDER/$ELAPSED_TIME_FILE"

for test_case in "${TEST_CASES[@]}"
do
	echo "Running test case \"$test_case\""
  RESOURCES=$(run_test "$test_case" 2>&1)

  echo "Parsing time command output..."
  MEMORY_USAGE=$(echo "$RESOURCES" | grep "Maximum resident" | xargs | tr -dc '0-9')
  TIME_ELAPSED=$(echo "$RESOURCES" | grep "System time" | xargs | awk '{print $4 }')

  echo "Calculating execution time..."
  RND=$(shuf -i 1-10 -n 1)
  TIME_ELAPSED=$(echo "$TIME_ELAPSED * 1000 + $RND" | bc )

  echo "Updating maximum memory usage..."
  if [[ $MAX_MEMORY_USAGE -lt $MEMORY_USAGE ]]; then
    MAX_MEMORY_USAGE="$MEMORY_USAGE"
  fi

  echo "Updating maximum execution time..."
  if (( $(echo "$TIME_ELAPSED > $MAX_ELAPSED_TIME" | bc -l) )); then
    MAX_ELAPSED_TIME="$TIME_ELAPSED"
  fi
done

echo "$MAX_MEMORY_USAGE" > "$OUTPUT_FOLDER/$MEMORY_FILE"
echo "$MAX_ELAPSED_TIME" > "$OUTPUT_FOLDER/$ELAPSED_TIME_FILE"

echo "Output"
cat $OUTPUT_FOLDER/$RESULT_FILE

echo "Error"
cat $OUTPUT_FOLDER/$ERROR_FILE
