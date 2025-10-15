#!/bin/bash
npm install marked@4.1.1
node convertMarkdown.js
rm *.json
rm -rf node_modules