'use strict';

const v_cookies_keys = {
    zip_code: "qt_zip_code",
    own_input: "qt_own_input",
    spouse_input: "qt_spouse_input",
    dependents: "qt_dependents"
};

const v_templates = {
    children: '<router-view></router-view>', // for children templates
    zip_code: '#zipcode-template',
    root: '#root-template',
    survey_member: '#survey-template',
    survey_card: '#survey-card-template',
    monthly_income: '#monthly-income-template',
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
            /* all accepted key codes:
            * backspace: 8      * left arrow: 37
            * right arrow: 39   * del: 46
            * num pad: 96-105   * number: 48-57
            * */
            var kc = e.keyCode;  // console.log("prevent_NaN_input  " + kc)
            if (![8,37,39,46].includes(kc)) {
                // console.log("inside IF")
                if (this.inputs.dob.length >= 10 || !((kc >= 96 && kc <= 105) || (kc >= 48 && kc <= 57))){
                    // prevent user from inserting non number and no more than 10 character
                    // console.log("preventing")
                    e.preventDefault();
                }
            } //else console.log("Else")
        },
        auto_slash_insert: function (e) {
            this.current_stage = survey_card_stages[0];
            if (e.keyCode === 8 || e.keyCode === 46) {
                // if "backspace" or "del" button pressed
                if (this.inputs.dob.length === 2 || this.inputs.dob.length === 5) {
                    this.inputs.dob = this.inputs.dob.slice(0, -1)
                }
            } else if (this.inputs.dob.length === 2 || this.inputs.dob.length === 5) {
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
                console.warn("your age must be under " + this.prop_max_age +" years old !!")
            } else if (age < this.prop_min_age) {
                console.warn("your age must be at least " + this.prop_min_age);
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
                    /* all accepted key codes:
                    * backspace: 8      * left arrow: 37
                    * right arrow: 39   * del: 46
                    * num pad: 96-105   * number: 48-57
                    * */
                    var kc = e.keyCode;
                    if (![8,37,39,46].includes(kc)) {
                        if (!((kc >= 96 && kc <= 105) || (kc >= 48 && kc <= 57))){
                            // prevent user from inserting non number
                            e.preventDefault();
                        }
                    }
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
                        max_dependents: 9,
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
                    save_to_cookie: function() {
                        console.log("Hello there");
                        let _t = this;
                        _t.$cookies.set(v_cookies_keys.own_input, _t.own_input, 60 * 60 * 24);

                        if (_t.spouse)
                            _t.$cookies.set(v_cookies_keys.spouse_input, _t.spouse_input, 60 * 60 * 24);
                        else
                            _t.$cookies.remove(v_cookies_keys.spouse_input);

                        if (_t.dependents.length > 0)
                            _t.$cookies.set(v_cookies_keys.dependents, JSON.stringify(_t.dependents), 60 * 60 * 24)
                        else
                            _t.$cookies.remove(v_cookies_keys.dependents);



                    },
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

                    let cookie_own_input = this.$cookies.get(v_cookies_keys.own_input);
                    let cookie_spouse_input = this.$cookies.get(v_cookies_keys.spouse_input);
                    let cookie_dependents = this.$cookies.get(v_cookies_keys.dependents);

                    console.log("cookies:  " + JSON.stringify(cookie_own_input));
                    console.log("cookies:  " + JSON.stringify(cookie_spouse_input));
                    console.log("cookies:  " + JSON.stringify(cookie_dependents));


                    if(cookie_own_input)
                        this.own_input = cookie_own_input;

                    if(cookie_spouse_input)
                        this.spouse_input = cookie_spouse_input;

                    if(cookie_dependents) {
                        var cookie_dependents_input = JSON.parse(cookie_dependents);

                        for (var i=0; i<cookie_dependents_input.length; i++){
                            this.dependents.push({
                                dob: cookie_dependents_input[i].dob,
                                gender: cookie_dependents_input[i].gender,
                                tobacco: cookie_dependents_input[i].tobacco
                            })
                        }
                    }
/*                    this.own_input = {
                        dob: '',
                        gender: '',
                        tobacco: '',
                    };
                    this.spouse_input = {
                        dob: '',
                        gender: '',
                        tobacco: '',
                    };*/
                }
            },
            name: 'survey-member',
        },{
            path: 'income',
            component: {
                template: v_templates.monthly_income,
                data: function () {
                    return {
                        income: '',
                        max_dependents: 9
                    }
                },
                methods: {
                    accept_only_number: function (e) {
                        /* all accepted key codes:
                   * backspace: 8      * left arrow: 37
                   * right arrow: 39   * del: 46
                   * num pad: 96-105   * number: 48-57
                   * */
                        var kc = e.keyCode;
                        if (![8,37,39,46].includes(kc)) {
                            if (!((kc >= 96 && kc <= 105) || (kc >= 48 && kc <= 57))){
                                // prevent user from inserting non number
                                e.preventDefault();
                            }
                        }
                    },

                    redirect_to_plans: function(redirect_url, csrf_token) {
                        let _t = this;
                        let cookie_own_input = this.$cookies.get(v_cookies_keys.own_input);
                        let cookie_spouse_input = this.$cookies.get(v_cookies_keys.spouse_input);
                        let cookie_dependents = this.$cookies.get(v_cookies_keys.dependents);
                        let cookie_dependents_input = cookie_dependents ? JSON.parse(cookie_dependents) : null;

                        let form_data = {
                            Zip_Code: this.$cookies.get(v_cookies_keys.zip_code),   // TODO: recheck cookie value before this
                            Include_Spouse: cookie_spouse_input ? 'Yes': 'No',
                            Payment_Option: '1',
                            Ins_Type: 'lim',
                            'child-TOTAL_FORMS': cookie_dependents_input ? cookie_dependents_input.length : 0,
                            'child-INITIAL_FORMS': 0,   // TODO: this would be initialized from this.created()
                            'child-MIN_NUM_FORMS': 0,
                            'child-MAX_NUM_FORMS': this.max_dependents,
                        };
                        if(Object.keys(cookie_own_input).every((k) => cookie_own_input[k])){    // checking if all data present for applicant
                            form_data['Applicant_DOB'] = cookie_own_input.dob;
                            form_data['Applicant_Gender'] = cookie_own_input.gender;
                            form_data['Tobacco'] = cookie_own_input == 'true' ? 'Y' : 'N';
                            form_data['Children_Count'] = cookie_dependents_input ? cookie_dependents_input.length : 0;

                            var newDate = new Date();
                            newDate.setDate(newDate.getDate() + 1);
                            form_data['Effective_Date'] = (newDate.getMonth() + 1) + '/' + newDate.getDate() + '/' +  newDate.getFullYear();

                        } else {
                            console.error("Please insert data to see plans");
                            return null;
                        }
                        if (cookie_spouse_input) {
                            if (Object.keys(cookie_spouse_input).every((k) => cookie_spouse_input[k])) { // check spouse data
                                form_data['Spouse_DOB'] = cookie_spouse_input.dob;
                                form_data['Spouse_Gender'] = cookie_spouse_input.gender;
                                form_data['Spouse_Tobacco'] = cookie_spouse_input.tobacco == 'true' ? 'Y' : 'N';  // TODO: Implement spouse tobacco in forms/views
                            } else {
                                console.error("Please insert spouse data correctly to see plans");
                                return null;
                            }cookie_dependents_input ? cookie_dependents_input.length : 0;
                        }
                        if(cookie_dependents_input) {
                            for(var i=0; i<cookie_dependents_input.length; i++){
                                if (Object.keys(cookie_dependents_input[i]).every((k) => cookie_dependents_input[i][k])) {

                                    form_data['child-' + i + '-Child_DOB'] = cookie_dependents_input[i].dob;
                                    form_data['child-' + i + '-Child_Gender'] = cookie_dependents_input[i].gender;
                                    form_data['child-' + i + '-Child_Tobacco'] = cookie_dependents_input[i].tobacco == 'true';

                                } else {
                                    console.error("Please insert child data correctly to see plans");
                                    return null;
                                }
                            }
                        }


                        console.table(form_data);
                        console.log("Redirect URL is: "+ redirect_url);
                        $.ajax({
                            url: redirect_url,
                            method: 'post',
                            dataType: 'json',
                            beforeSend: function (xhr) {
                                xhr.setRequestHeader("X-CSRFToken", csrf_token);
                            },
                            data: form_data,
                            success: function (data) {
                                console.log("Success");
                                // console.table(data);
                                if(data.url) {
                                    console.log("Navigating to "+ data.url);
                                    location.href = data.url;
                                }
                                else {
                                    // console.error("XXXXXX");
                                    router.push({name: 'survey-member'});
                                }
                            },
                            error: function(data) {
                                console.log("Error");
                                console.table(data);
                            }

                        })
                    }
                }
            },
            name: 'survey-income',
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

router.afterEach((to, from) => {
    window.scrollTo(0, 0); // if url changed scroll to TOP
});
