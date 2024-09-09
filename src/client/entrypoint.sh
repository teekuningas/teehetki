#!/bin/sh

echo "Replacing RUNTIME_API_ADDRESS in JS files"
find /app/build -type f | while IFS= read -r file; do
  if [ -f "$file" ]; then
    sed -i "s|%%RUNTIME_API_ADDRESS%%|${API_ADDRESS:-ws://localhost:5000}|g" $file
  fi
done

echo "Replacing RUNTIME_PREFIX_PATH in JS files"
find /app/build -type f | while IFS= read -r file; do
  sed -i "s|/%%RUNTIME_PREFIX_PATH%%|${PREFIX_PATH:-}|g" $file
done
find /app/build -type f | while IFS= read -r file; do
  sed -i "s|%%RUNTIME_PREFIX_PATH%%|${PREFIX_PATH:-}|g" $file
done

if [ -n "$PREFIX_PATH" ]; then
  mkdir -p /app/build${PREFIX_PATH}
  mv /app/build/* /app/build${PREFIX_PATH}/
fi

exec "$@"
