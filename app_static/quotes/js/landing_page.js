'use strict';

const v_templates = {
    children: '<router-view></router-view>', // for children templates
    zip_code: '#zipcode-template',
    root: '#root-template',
    survey_member: '#survey-template',
};

const svg_format = (svg_attr, path_d) => {
    let attrs = '';
    for (let k in svg_attr) {
        attrs += ` ${k}="${svg_attr[k]}" `;
    }
    return `<svg xmlns="http://www.w3.org/2000/svg" ${attrs}><path d="${path_d}"></path></svg>`
};

const marker = {
    success_icon: svg_format(
        {class: "success", viewBox: '0 0 24 24'},
        "M20.285 2l-11.285 11.567-5.286-5.011-3.714 3.716 9 8.728 15-15.285z"),
    error_icon: svg_format(
        {class: "danger", viewBox: '0 0 24 24'},
        "M24 20.188l-8.315-8.209 8.2-8.282-3.697-3.697-8.212 8.318-8.31-8.203-3.666 3.666 8.321 8.24-8.206 8.313 3.666 3.666 8.237-8.318 8.285 8.203z"),
};

const router = new VueRouter({
    routes: [{
        path: '/',
        name: 'root',
        component: {
            template: v_templates.root,
            data: function () {
                return {
                    zip_placeholder: 'Enter Zip Code',
                    zip_code: '',
                    is_valid_zip: false,
                    current_marker: undefined,
                }
            },
            methods: {
                validate_zip: function (e) {
                    if (e.keyCode > 31 && (e.keyCode < 48 || e.keyCode > 57)) e.preventDefault();   // prevent if not number
                    else return true;
                },
                check_zipcode: function () {
                    if (this.is_valid_zip) {
                        router.push({name: 'survey-member'});
                    } else {

                    }
                }
            },
            watch: {
                zip_code: function () {
                    if (this.zip_code.length === 5) {
                        this.current_marker = marker.success_icon;
                        this.is_valid_zip = true;
                    } else {
                        this.current_marker = marker.error_icon;
                        this.is_valid_zip = false;
                    }
                }
            },
        },
    }, {
        path: '/health-insurance',
        name: 'survey',
        component: {
            template: v_templates.children,
        },
        children: [{
            path: 'member',
            component: {
                template: v_templates.survey_member,
                data: function () {
                    return {
                        dob: "",
                        gender: "",
                        tobacco: "",
                        spouse: "",
                        dependents: "",
                    }
                },
                methods: {
                    add_spouse() {
                        console.log("Adding spouse")
                    },
                },
                created() {
                    //check zip code
                }
            },
            name: 'survey-member',
        },]
    },]
});