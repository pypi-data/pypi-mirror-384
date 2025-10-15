$(document).ready(() => {
    'use strict';

    /**
     * Extend links to external website.
     * » add target="_blank"
     * » add rel="noopener noreferer"
     */
    const externalLinks = () => {
        // Get the current location hostname
        const internalHost = [location.hostname];

        // Regex pattern to match HTTP and HTTPS
        const protocolPattern = /^https?:\/\//i;

        // Walk through all links on the current page.
        $('a').each((index, element) => {
            // Get the href attribute of the link
            const href = $(element).attr('href');

            // Check if it's an HTTP link
            if (protocolPattern.test(href)) {
                // Get the hostname of the link
                const hrefHostname = $(new URL(href)).attr('hostname');

                // Check if the hostname is not in the internalHost array and add the target and rel attributes to the link element.
                if ($.inArray(hrefHostname, internalHost) === -1) {
                    $(element).attr('target', '_blank');
                    $(element).attr('rel', 'noopener noreferer');
                }
            }
        });
    };

    /**
     * Render a JS clock for EVE time.
     *
     * @param {Element} element The HTML element to display the time
     */
    const renderClock = (element) => {
        const date = new Date();

        /**
         * Date
         * @type {string} 2021-01-01
         */
        // const year = date.getUTCFullYear();
        // const month = String(date.getUTCMonth() + 1).padStart(2, '0');
        // const day = String(date.getUTCDate()).padStart(2, '0');

        /**
         * Time
         * @type {string} 00:00:00
         */
        const hour = String(date.getUTCHours()).padStart(2, '0');
        const minute = String(date.getUTCMinutes()).padStart(2, '0');
        const second = String(date.getUTCSeconds()).padStart(2, '0');

        element.html(hour + ':' + minute + ':' + second);
    };

    /**
     * Check if an element has CSS overflow.
     *
     * Usage:
     * ```js
     * const element = $('#element');
     * const {
     *     overflow, horizontal, vertical
     * } = elementHasOverflow(element);
     * ```
     *
     * @param {Element} element The element to check
     * @returns {{overflow: boolean, horizontal: boolean, vertical: boolean}} An object with the results.
     * `overflow` is true if the element has overflow,
     * `horizontal` is true if the element has horizontal overflow,
     * and `vertical` is true if the element has vertical overflow.
     */
    const elementHasOverflow = (element) => {
        const clientHeight = element[0].clientHeight;
        const scrollHeight = element[0].scrollHeight;
        const clientWidth = element[0].clientWidth;
        const scrollWidth = element[0].scrollWidth;

        return {
            overflow: clientHeight < scrollHeight || clientWidth < scrollWidth,
            horizontal: clientWidth < scrollWidth,
            vertical: clientHeight < scrollHeight
        };
    };

    /**
     * Toggle overflow classes on an element.
     * Adds the class `overflowing` if the element has overflow,
     * `overflowing-vertically` if it has vertical overflow,
     * and `overflow-horizontally` if it has horizontal overflow.
     *
     * @param {jQuery|Element} element The element to check
     */
    const toggleOverflowClasses = (element) => {
        if (element.length === 0) {
            return;
        }

        const currentClasses = element.attr('class') || '';
        const hasOverflowingClass = currentClasses.includes('overflowing');

        // Check if the element has overflow
        const {
            overflow, horizontal, vertical
        } = elementHasOverflow(element);

        // Only modify classes if the state has actually changed
        if (overflow) {
            const newClasses = ['overflowing'];

            if (vertical) {
                newClasses.push('overflowing-vertically');
            }

            if (horizontal) {
                newClasses.push('overflow-horizontally');
            }

            const currentOverflowClasses = currentClasses.match(/\b(overflowing(?:-vertically)?|overflow-horizontally)\b/g) || [];
            const newClassesSet = new Set(newClasses);
            const currentClassesSet = new Set(currentOverflowClasses);

            if (
                !newClasses.every((cls) => currentClassesSet.has(cls))
                || !currentOverflowClasses.every((cls) => newClassesSet.has(cls)) // jshint ignore:line
            ) {
                // Remove existing overflow classes and add the new ones
                element.removeClass('overflowing overflowing-vertically overflow-horizontally');
                element.addClass(newClasses.join(' '));
            }
        } else {
            if (hasOverflowingClass) {
                element.removeClass('overflowing overflowing-vertically overflow-horizontally');
            }
        }
    };

    /**
     * Inject a blurred background to the body.
     */
    const injectBlurBodyBackground = () => {
        $('<div class="blur-background"></div>').prependTo('body');
    };

    /**
     * Functions that need to be executed on successful ajax events.
     */
    $(document).ajaxSuccess(() => {
        externalLinks();
    });

    /**
     * Functions that need to be executed when the page is loaded.
     */
    (() => {
        injectBlurBodyBackground();

        // Start the Eve-time clock in the top menu bar.
        setInterval(() => {
            renderClock($('.eve-time-wrapper .eve-time-clock'));
        }, 500);

        externalLinks();

        /**
         * Set up overflow detection and monitoring for an element
         *
         * @param {string} selector CSS selector for the element
         */
        const setupOverflowMonitoring = (selector) => {
            const element = $(selector);

            if (element.length === 0) {
                return;
            }

            toggleOverflowClasses(element);

            // Use ResizeObserver for immediate size change detection
            const resizeObserver = new ResizeObserver(() => { // jshint ignore:line
                // Add a small delay to allow for smoother transitions
                requestAnimationFrame(() => {
                    toggleOverflowClasses(element);
                });
            });
            resizeObserver.observe(element[0]);

            // Optimized MutationObserver for content changes
            const mutationObserver = new MutationObserver(() => {
                toggleOverflowClasses(element);
            });

            mutationObserver.observe(element[0], {
                childList: true,
                subtree: true,
                characterData: true
            });
        };

        [
            '#aa-dashboard-panel-characters div.card-body > div:nth-child(2) > div',
            '#aa-dashboard-panel-membership div.card-body > div:nth-child(2) > div',
            'ul#sidebar-menu'
        ].forEach(setupOverflowMonitoring);

        console.log('Terra Nanotech JS: Loaded');
    })();
});
