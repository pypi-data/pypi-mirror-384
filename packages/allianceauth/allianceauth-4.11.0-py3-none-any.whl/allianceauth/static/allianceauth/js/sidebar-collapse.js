$(document).ready(() => {
    'use strict';

    const activeChildMenuItem = document.querySelector('ul#sidebar-menu ul.collapse a.active');

    if (activeChildMenuItem) {
        const activeChildMenuUl = activeChildMenuItem.closest('ul');
        activeChildMenuUl.classList.add('show');

        document.querySelectorAll(`[data-bs-target^="#${activeChildMenuUl.id}"]`)
            .forEach(element => element.setAttribute('aria-expanded', true));
    }
});
