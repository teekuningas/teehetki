#!/bin/sh

echo "Replacing env variables in JS files"
for file in /app/build/static/js/*.js; do
  if [ -f "$file" ]; then
    sed -i "s|%%RUNTIME_API_ADDRESS%%|${API_ADDRESS:-ws://localhost:5000}|g" $file
  fi
done

exec "$@"
