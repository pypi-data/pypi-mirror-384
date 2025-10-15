/* global CopyButtonPlugin */

// Load the required libraries
import hljs from '../libs/highlightjs/11.10.0/es/highlight.min.js';

$(document).ready(() => {
    'use strict';
    // Highlight code blocks with highlight.js
    if (typeof hljs !== 'undefined' && typeof hljs.highlightElement === 'function') {
        // Add the copy button plugin to highlight.js
        hljs.addPlugin(new CopyButtonPlugin());

        // Get all code blocks and highlight them
        document.querySelectorAll('pre code[class*="language-"]').forEach((block) => {
            const match = block.className.match(/language-(\w+)/);
            const language = match ? match[1] : null;

            if (language) {
                hljs.highlightElement(block, {language: language});
            }
        });
    }
});
