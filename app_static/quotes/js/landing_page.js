'use strict';

const v_cookies_keys = {
    zip_code: "qt_zip_code",
};

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
        inputs:{
            type: Object,
            default: () => ({
                dob: '',
                gender: '',
                tobacco: '',
            }),
        },
    },
    data: function () {
        return {
            current_stage: this.prop_current_stage,
            gg: this.inputs,
        }
    },
    created: function(){
        this.check_age();
    },
    watch: {
        inputs: function(val, oldVal) {
            this.check_age();
        }
    },
    methods: {
        txt_whos: function () {
            // return "your" or "his/her" depending on who is the insurance holder
            return this.survey_type === holder_types_enum.own ? "your" : "his/her";
        },
        prevent_NaN_input: function (e) {
            if (this.inputs.dob.length >= 10 || (e.keyCode < 48 || e.keyCode > 57)) {
                // prevent user from inserting non number and no more than 10 character
                e.preventDefault();
            }
        },
        auto_slash_insert: function () {
            this.current_stage = survey_card_stages[0];
            if (this.inputs.dob.length === 2 || this.inputs.dob.length === 5) {
                if (this.inputs.dob[this.inputs.dob.length - 1] !== '/') {
                    this.inputs.dob += '/';
                }
            } else if (this.inputs.dob.length >= 10) {
                this.check_age();
            }
        },
        check_age: function () {
            //Your age must be under 99 years old
            // Your age must be at least 21
            var dob = new Date(this.inputs.dob);
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
                if (this.inputs.gender) this.current_stage = survey_card_stages[2];
            }
        },
        remove_component: function (holder_type, idx) {
            if(holder_type === this.$parent.holder_types_enum.child){
                this.$parent.remove_dependent(idx);
            }else if(holder_type === this.$parent.holder_types_enum.spouse) {
                this.$parent.spouse = false;
            }
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
            created: function(){
                let cookie_zip = this.$cookies.get(v_cookies_keys.zip_code);
                if(cookie_zip){
                    this.zip_code = cookie_zip;
                    this.is_valid_zip = true;
                }
            },
            methods: {
                validate_zip: function (e) {
                    if (e.keyCode > 31 && (e.keyCode < 48 || e.keyCode > 57)) e.preventDefault();   // prevent if not number
                    else return true;
                },
                check_zipcode: function () {
                    if (this.is_valid_zip) {
                        this.$cookies.set(v_cookies_keys.zip_code, this.zip_code, 60 * 60 * 24);
                        router.push({name: 'survey-member'});
                    } else {
                        this.$cookies.remove(v_cookies_keys.zip_code);
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
                        own_input: {
                            dob: '',
                            gender: '',
                            tobacco: '',
                        },
                        spouse: false,
                        spouse_input: {
                            dob: '',
                            gender: '',
                            tobacco: '',
                        },
                        dependents: [],
                        max_dependents: 5,
                    }
                },
                methods: {
                    add_dependent: function () {
                        this.dependents.push({
                            dob: "",
                            gender: '',
                            tobacco: '',
                        });
                    },
                    remove_dependent: function(idx) {
                        this.dependents.splice(idx, 1);
                    },
                    redirect_to_plans: function(redirect_url, csrf_token) {
                        let _t = this;
                        let form_data = {
                            zip_code: this.$cookies.get(v_cookies_keys.zip_code),   // TODO: recheck cookie value before this
                        };
                        if(Object.keys(_t.own_input).every((k) => _t.own_input[k])){    // checking if all data present for applicant
                            form_data['applicant_dob'] = _t.own_input.dob;
                            form_data['applicant_gender'] = _t.own_input.gender;
                            form_data['applicant_tobacco'] = _t.own_input.tobacco == 'true';
                        } else {
                            console.error("Please insert data to see plans");
                            return null;
                        }
                        if (_t.spouse) {
                            if (Object.keys(_t.spouse_input).every((k) => _t.spouse_input[k])) { // check spouse data
                                form_data['spouse_dob'] = _t.spouse_input.dob;
                                form_data['spouse_gender'] = _t.spouse_input.gender;
                                form_data['spouse_tobacco'] = _t.spouse_input.tobacco == 'true';
                            } else {
                                console.error("Please insert spouse data correctly to see plans");
                                return null;
                            }
                        }
                        if(_t.dependents.length > 0) {
                            let child_data = [];
                            for(var i=0; i<_t.dependents.length; i++){
                                if (Object.keys(_t.dependents[i]).every((k) => _t.dependents[i][k])) {
                                    child_data.push({
                                        'child_dob': _t.dependents[i].dob,
                                        'child_gender': _t.dependents[i].gender,
                                        'child_tobacco': _t.dependents[i].tobacco == 'true',
                                    });
                                } else {
                                    console.error("Please insert child data correctly to see plans");
                                    return null;
                                }
                            }
                            form_data['children'] = child_data;
                        }
                        console.table(form_data);
                        console.log("Welcome to the jungle!");
                        console.log("Redirect URL is: "+ redirect_url)

                        $.ajax({
                            url: redirect_url,
                            method: 'get',
                            headers: {
                                'X-CSRFToken': csrf_token,
                                'Content-Type': 'application/json',
                            },
                            data: form_data,
                        })
                        
                        /*axios({
                            method: 'post',
                            url: redirect_url,
                            headers: {
                                'X-CSRFToken': csrf_token,
                                'Content-Type': 'application/json',
                            },
                            data: {"GG":true},
                        })
                        .then(function(response){
                            console.log("Response: "+ response.status); // TODO DEBUG
                            if (response.status === 200) {
                                console.log("Redirecting");
                                window.location = redirect_url;
                            }

                        })*/
                    }
                },
                watch: {
                    spouse_input: function () {
                        this.spouse = !!this.spouse_input.dob;  // if found previous data, then show spouse card
                    },
                },
                created() {
                    let zip_code = this.$cookies.get(v_cookies_keys.zip_code);
                    console.log("cookies:  " + zip_code);
                    if(!zip_code){
                        router.push({name: 'root'});
                    }
                }
            },
            name: 'survey-member',
        },]
    },{
        path: '/dashboard',
        component: {
            created: function () {
                window.location = '/dashboard/';
            }
        }
    },{
        path: '/login',
        component: {
            created: function () {
                window.location = '/login/';
            }
        }
    },{
        path: '*',
        redirect: '/'
    },]
});