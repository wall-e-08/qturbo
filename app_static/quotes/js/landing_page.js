'use strict';

const v_templates = {
    children: '<router-view></router-view>', // for children templates
    zip_code: '#zipcode-template',
    root: '#root-template',
    survey_member: '#survey-template',
    survey_card: '#survey-card-template',
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

const holder_types_enum = {
    own: "me",
    spouse: "spouse",
    child: "dependent"
};

const survey_card_stages = ["dob", "gender", "tobacco"]

const v_survey_card = {
    delimiters: ['[[', ']]'],
    props: {
        index: {    // needs only for dependents list
            default: 0,
            type: Number,
        },
        survey_type: {
            validator: function (val) {
                // The value must match one of the value of holder_types_enum
                for (var key in holder_types_enum) {
                    if (holder_types_enum[key] === val) {
                        return true;
                    }
                }
                return false;
            }
        },
        current_stage: {
            validator: function (val) {
                // The value must match one of these strings
                return survey_card_stages.indexOf(val) !== -1
            }
        },
    },
    data: function () {
        return {}
    },
    methods: {
        txt_whos: function () {
            // return "your" or "his/her" depending on who is the insurance holder
            return this.survey_type === holder_types_enum.own ? "your" : "his/her";
        }
    },
    template: v_templates.survey_card
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
        children: [{    // this is path-children, it's not dependent
            path: 'member',
            component: {
                template: v_templates.survey_member,
                components: {
                    'survey-card': v_survey_card,
                },
                data: function () {
                    return {
                        holder_types_enum: holder_types_enum,
                        spouse: false,
                        dependents: [],
                        max_dependents: 5,
                    }
                },
                methods: {
                    add_spouse: function () {
                        this.spouse = true;
                    },
                    add_dependent: function () {
                        this.dependents.push('baccha');
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