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

const survey_card_stages = ["dob", "gender", "tobacco"];

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
        prop_current_stage: {
            validator: function (val) {
                // The value must match one of these strings
                return survey_card_stages.indexOf(val) !== -1
            }
        },
        prop_max_age: {
            type: Number,
            required: true,
            default: 99,
        },
        prop_min_age: {
            type: Number,
            required: true,
            default: 21,
        },
    },
    data: function () {
        return {
            current_stage: this.prop_current_stage,
            dob: "",
            gender: '',
            tobacco: '',
        }
    },
    watch: {
        gender: function () {
            if (this.gender) this.current_stage = survey_card_stages[2];
        },
    },
    methods: {
        txt_whos: function () {
            // return "your" or "his/her" depending on who is the insurance holder
            return this.survey_type === holder_types_enum.own ? "your" : "his/her";
        },
        prevent_NaN_input: function (e) {
            if (this.dob.length >= 10 || (e.keyCode < 48 || e.keyCode > 57)) {
                // prevent user from inserting non number and no more than 10 character
                e.preventDefault();
            }
        },
        auto_slash_insert: function () {
            this.current_stage = survey_card_stages[0];
            if (this.dob.length === 2 || this.dob.length === 5) {
                if (this.dob[this.dob.length - 1] !== '/') {
                    this.dob += '/';
                }
            } else if (this.dob.length >= 10) {
                this.check_age();
            }
        },
        check_age: function () {
            //Your age must be under 99 years old
            // Your age must be at least 21
            var dob = new Date(this.dob);
            if (dob == 'Invalid Date') {
                console.warn("invalid date");
                return false;
            }
            var age = Math.floor((new Date() - dob) / (365 * 24 * 60 * 60 * 1000));
            if (age > this.prop_max_age) {
                console.warn("your age must be under 99 years old !!")
            } else if (age < this.prop_min_age) {
                console.warn("your age must be at least 21");
            } else {
                this.current_stage = survey_card_stages[1];
                if (this.gender) this.current_stage = survey_card_stages[2];
            }
        },
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
                        my_dob: '',
                        spouse_dob: '',
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
                    remove_survey_card: function (holder_type, key=0) {
                        console.log(holder_type);
                        console.warn(key);
                        if (holder_type === this.holder_types_enum.spouse) {
                            this.spouse = false;
                        } else if(holder_type === this.holder_types_enum.child){
                            this.dependents.splice(key, 1)
                        }
                    }
                },
                created() {
                    //check zip code
                }
            },
            name: 'survey-member',
        },]
    },]
});