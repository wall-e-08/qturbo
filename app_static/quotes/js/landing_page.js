'use strict';

const v_templates = {
    zip_code: '#zipcode-template',
    root: '#root-template',
};

const svg_format = (svg_attr, path_d) => {
    let attrs = '';
    for (let k in svg_attr) {
        attrs += ` ${k}="${svg_attr[k]}" `;
    }
    return `<svg xmlns="http://www.w3.org/2000/svg" ${attrs}><path d="${path_d}"/></svg>`
};

const marker = {
    success_icon: svg_format(
        {class: "success", viewBox: '0 0 24 24'},
        "M20.285 2l-11.285 11.567-5.286-5.011-3.714 3.716 9 8.728 15-15.285z"),
    error_icon: svg_format(
        {class: "danger", viewBox: '0 0 24 24'},
        "M24 20.188l-8.315-8.209 8.2-8.282-3.697-3.697-8.212 8.318-8.31-8.203-3.666 3.666 8.321 8.24-8.206 8.313 3.666 3.666 8.237-8.318 8.285 8.203z"),
};

Vue.component('zip-code', {
    delimiters: ['[[', ']]'],
    data: function () {
        return {
            placeholder: 'Enter Zip Code',
            zip_code: '',
            current_marker: undefined,
        }
    },
    methods: {
        validate_zip: function (e) {
            if (e.keyCode > 31 && (e.keyCode < 48 || e.keyCode > 57)) e.preventDefault();   // prevent if not number
            else return true;
        }
    },
    watch: {
        zip_code: function () {
            if (this.zip_code.length === 5) {
                this.current_marker = marker.success_icon;
            } else {
                this.current_marker = marker.error_icon;
            }
        }
    },
    template: v_templates.zip_code,
});

const router = new VueRouter({
    routes: [{
        path: '/',
        component: {
            template: v_templates.root,
        },
        name: 'root',
    }, /*{
        path: '/fff',
        component: ppp,
        name: 'parent',
        children: [{
            path: 'ggg',
            component: cccc,
            name: 'child',
        },]
    },*/]
});