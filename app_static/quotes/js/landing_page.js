'use strict';

const v_all_routes_name = {
    root: 'root',
    zip: 'zip-code',
    survey: 'survey',
    quote: 'survey-member',
    plan_type: 'survey-plan',
    income: 'survey-income',
};

const v_cookies_keys = {
    zip_code: "qt_zip_code",
    plan_type: "qt_plan_type",
    own_input: "qt_own_input",
    spouse_input: "qt_spouse_input",
    dependents: "qt_dependents"
};

const v_templates = {
    children: '<router-view></router-view>', // for children templates
    root: '#root-template',
    zip_code: '#zipcode-template',
    survey_member: '#survey-template',
    survey_card: '#survey-card-template',
    plan_type: '#plan-type-template',
    annual_income: '#annual-income-template',
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
            dob_err: '',
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
            this.dob_err = '';
            this.current_stage = survey_card_stages[0];
            this.inputs.gender = '';
            this.inputs.tobacco = '';
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
            var dob = new Date(this.inputs.dob);
            if (dob == 'Invalid Date') {
                if(this.inputs.dob) {
                    this.dob_err = 'Invalid Date';   // don't show error if input is empty
                    this.$parent.show_error = true;
                } else {
                    this.dob_err = '';
                    this.$parent.show_error = false;
                }
                // console.warn("invalid date");
                return false;
            }
            var age = Math.floor((new Date() - dob) / (365 * 24 * 60 * 60 * 1000));
            if (age > this.prop_max_age) {
                this.dob_err = "Your age must be under " + this.prop_max_age +" years old !";
                this.$parent.show_error = true;
            } else if (age < this.prop_min_age) {
                this.dob_err = "Your age must be at least " + this.prop_min_age + " years !";
                this.$parent.show_error = true;
            } else {
                this.dob_err = '';
                this.$parent.show_error = false;
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
        name: v_all_routes_name.root,
        component: {
            template: v_templates.root,
        }
    }, {
        path: '/zip-code',
        name: v_all_routes_name.zip,
        component: {
            template: v_templates.zip_code,
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
                    * ctrl key: 17      * cmd key: 91
                    * V: 86             * C key: 67
                    * */
                    var kc = e.keyCode;
                    if (![8,37,39,46,17,91,86].includes(kc)) {
                        if (!((kc >= 96 && kc <= 105) || (kc >= 48 && kc <= 57))){
                            // prevent user from inserting non number
                            e.preventDefault();
                        }
                    }
                },
                check_zipcode: function () {
                    let _t = this;
                    let id_loading_overlay = document.getElementById('overlay-loading');
                    id_loading_overlay.style.display = "block";

                    if (_t.is_valid_zip) {
                        setTimeout(function () {
                            id_loading_overlay.style.display = "none";
                            _t.$cookies.set(v_cookies_keys.zip_code, _t.zip_code, 60 * 60 * 24);
                            router.push({name: v_all_routes_name.quote});
                        }, 1000);
                    } else {
                        setTimeout(function () {
                            _t.$cookies.remove(v_cookies_keys.zip_code);
                            id_loading_overlay.style.display = "none";
                        }, 1000);
                    }
                },
                on_paste_zip: function () {
                    let _t = this;
                    setTimeout(function () {
                        if(!(_t.zip_code.length !== 5 && !isNaN(_t.zip_code)) && !_t.is_valid_zip)
                            _t.zip_code = '';
                    }, 50); // settimeout is using because of updating delay after paste item
                }
            },
            watch: {
                zip_code: function () {
                    if (this.zip_code.length === 5 && !isNaN(this.zip_code)) {
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
        name: v_all_routes_name.survey,
        component: {
            template: v_templates.children,
        },
        children: [{    // this is path-children, it's not dependent
            path: 'member',
            name: v_all_routes_name.quote,
            component: {
                template: v_templates.survey_member,
                delimiters: ['[[', ']]'],
                components: {
                    'survey-card': v_survey_card,
                },
                data: function () {
                    return {
                        holder_types_enum: holder_types_enum,
                        show_error: false,  // form validation error
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
                        dependents_data_correct: false,
                        max_dependents: 9,
                        err_msg: '',    // ajax error
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
                    start_celery_quote: function(redirect_url, csrf_token) {
                        let _t = this;
                        let form_data = {
                            Zip_Code: this.$cookies.get(v_cookies_keys.zip_code),   // TODO: recheck cookie value before this @torsho
                            Include_Spouse: this.spouse ? 'Yes': 'No',
                            Payment_Option: '1',
                            Ins_Type: 'lim',
                            'child-TOTAL_FORMS': this.dependents.length,
                            'child-INITIAL_FORMS': 0,
                            'child-MIN_NUM_FORMS': 0,
                            'child-MAX_NUM_FORMS': this.max_dependents,
                        };
                        let id_loading_overlay = document.getElementById('overlay-loading');

                        id_loading_overlay.style.display = "block";
                        _t.err_msg = '';
                        if(Object.keys(_t.own_input).every((k) => _t.own_input[k])){    // checking if all data present for applicant
                            form_data['Applicant_DOB'] = _t.own_input.dob;
                            form_data['Applicant_Gender'] = _t.own_input.gender;
                            form_data['Tobacco'] = _t.own_input.tobacco == 'true' ? 'Y' : 'N';
                            form_data['Children_Count'] = _t.dependents.length;

                            var newDate = new Date();
                            newDate.setDate(newDate.getDate() + 1);
                            form_data['Effective_Date'] = (newDate.getMonth() + 1) + '/' + newDate.getDate() + '/' +  newDate.getFullYear();

                        } else {
                            // console.error("Please insert data to see plans");
                            return null;
                        }
                        if (_t.spouse) {
                            if (Object.keys(_t.spouse_input).every((k) => _t.spouse_input[k])) { // check spouse data
                                form_data['Spouse_DOB'] = _t.spouse_input.dob;
                                form_data['Spouse_Gender'] = _t.spouse_input.gender;
                                form_data['Spouse_Tobacco'] = _t.spouse_input.tobacco == 'true' ? 'Y' : 'N';
                            } else {
                                // console.error("Please insert spouse data correctly to see plans");
                                return null;
                            }
                        }
                        if(_t.dependents.length > 0) {
                            for(var i=0; i<_t.dependents.length; i++){
                                if (Object.keys(_t.dependents[i]).every((k) => _t.dependents[i][k])) {
                                    form_data['child-' + i + '-Child_DOB'] = _t.dependents[i].dob;
                                    form_data['child-' + i + '-Child_Gender'] = _t.dependents[i].gender;
                                    form_data['child-' + i + '-Child_Tobacco'] = _t.dependents[i].tobacco == 'true' ? 'Y' : 'N';
                                } else {
                                    // console.error("Please insert child data correctly to see plans");
                                    return null;
                                }
                            }
                        }
                        $.ajax({
                            url: redirect_url,
                            method: 'post',
                            dataType: 'json',
                            beforeSend: function (xhr) {
                                xhr.setRequestHeader("X-CSRFToken", csrf_token);
                            },
                            data: form_data,
                            success: function (data) {
                                // console.log("Initial success");
                                // console.table(data);
                                if (data.status === "false"){
                                    // console.log("Error in form data");
                                    // console.table(data.errors);
                                    setTimeout(function () {
                                         _t.err_msg = "Internal Server error!";
                                        id_loading_overlay.style.display = "none";
                                    }, 1000);
                                } else {
                                    setTimeout(function () {
                                        router.push({name: v_all_routes_name.plan_type});
                                        id_loading_overlay.style.display = "none";
                                    }, 1000);
                                }
                            },
                            error: function(data) {
                                // console.log("Error");
                                // console.table(data);
                                setTimeout(function () {
                                    if(data.message) _t.err_msg = data.message;
                                    else  _t.err_msg = "Unexpected Error occurred!";
                                    id_loading_overlay.style.display = "none";
                                }, 1000);
                            }
                        })
                    },
                },
                watch: {
                    spouse_input: function () {
                        this.spouse = !!this.spouse_input.dob;  // if found previous data, then show spouse card
                    },
                    dependents: {
                        handler() {
                            let _t = this;
                            for (let i = 0; i < _t.dependents.length; i++) {
                                _t.dependents_data_correct = Object.keys(_t.dependents[i]).every((k) => _t.dependents[i][k]);
                            }
                        },
                        deep: true
                    }
                },
                computed: {
                    is_all_data_valid: function () {
                        return this.own_input.dob && this.own_input.gender && this.own_input.tobacco &&
                            (!this.spouse || (this.spouse_input.dob && this.spouse_input.gender && this.spouse_input.tobacco)) &&
                            ((!this.dependents.length) || this.dependents_data_correct);
                    }
                },
                created() {
                    let zip_code = this.$cookies.get(v_cookies_keys.zip_code);
                    let cookie_own_input = this.$cookies.get(v_cookies_keys.own_input);
                    let cookie_spouse_input = this.$cookies.get(v_cookies_keys.spouse_input);
                    let cookie_dependents = this.$cookies.get(v_cookies_keys.dependents);
                    // console.log("cookies(zip):  " + zip_code);
                    // console.log("cookies(own):  " + JSON.stringify(cookie_own_input));
                    // console.log("cookies(spouse):  " + JSON.stringify(cookie_spouse_input));
                    // console.log("cookies(childs):  " + JSON.stringify(cookie_dependents));

                    if(!zip_code){
                        router.push({name: v_all_routes_name.zip});
                    }

                    if(cookie_own_input)
                        this.own_input = cookie_own_input;

                    if(cookie_spouse_input)
                        this.spouse_input = cookie_spouse_input;

                    let cookie_dependents_input = {};
                    if(cookie_dependents) {
                        cookie_dependents_input = JSON.parse(cookie_dependents);

                        for (var i=0; i<cookie_dependents_input.length; i++){
                            this.dependents.push({
                                dob: cookie_dependents_input[i].dob,
                                gender: cookie_dependents_input[i].gender,
                                tobacco: cookie_dependents_input[i].tobacco
                            })
                        }
                    }
                }
            },
        },{
            path: 'plan',
            name: v_all_routes_name.plan_type,
            component: {
                delimiters: ['[[', ']]'],
                template: v_templates.plan_type,
                data: function () {
                    return {
                        plan_type: '',
                        err_msg: '',
                        stm_avail: '',
                        lim_avail: '',
                    }
                },
                created: function(){
                    let _t = this;
                    let zip_code = _t.$cookies.get(v_cookies_keys.zip_code);

                    _t.stm_avail = true;
                    _t.lim_avail = true;

                    let data = {
                        'zip_code': zip_code
                    };

                    $.ajax({
                        url: 'ins-avail-state/',
                        method: 'GET',
                        dataType: 'JSON',
                        data: data,
                        success: function (data) {
                            console.log("Initial success");
                            console.table(data);
                                _t.stm_avail = data.stm;
                                _t.lim_avail = data.lim;
                            console.log(_t.stm_avail);
                        },
                        error: function(data) {
                            // console.log("Error");
                            // console.table(data);
                        }
                    });

                },
                methods: {
                    choose_plan_type: function(redirect_url, csrf_token, plan_type) {
                        let _t = this;
                        let id_loading_overlay = document.getElementById('overlay-loading');
                        _t.plan_type = plan_type;
                        _t.err_msg = '';
                        id_loading_overlay.style.display = "block";

                        $.ajax({
                            url: redirect_url,
                            method: 'post',
                            dataType: 'json',
                            beforeSend: function (xhr) {
                                xhr.setRequestHeader("X-CSRFToken", csrf_token);
                            },
                            data: {
                                Ins_Type: plan_type
                            },
                            success: function (data) {
                                // console.log(`Set insurance type to ${plan_type}.`);
                                setTimeout(function () {
                                    id_loading_overlay.style.display = "none";
                                    router.push({name: v_all_routes_name.income});
                                }, 1000);
                            },
                            error: function(data) {
                                // console.log("Error");
                                // console.table(data);
                                setTimeout(function () {
                                    if(data.message) _t.err_msg = data.message;
                                    else  _t.err_msg = "Unexpected Error occurred!";
                                    id_loading_overlay.style.display = "none";
                                }, 1000);
                            }
                        });
                    },
                }
            }
        },{
            path: 'income',
            name: v_all_routes_name.income,
            component: {
                delimiters: ['[[', ']]'],
                template: v_templates.annual_income,
                data: function () {
                    return {
                        income: '',
                        max_dependents: 9,
                        err_msg: '',
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
                    redirect_to_plans: function (redirect_url, csrf_token, income) {
                        let _t = this;
                        let id_loading_overlay = document.getElementById('overlay-loading');
                        _t.income = income;
                        _t.err_msg = '';
                        id_loading_overlay.style.display = "block";

                        $.ajax({
                            url: redirect_url,
                            method: 'post',
                            dataType: 'json',
                            beforeSend: function (xhr) {
                                xhr.setRequestHeader("X-CSRFToken", csrf_token);
                            },
                            data: {
                                Annual_Income: income
                            },
                            success: function (data) {
                                if (data.url){
                                    // console.log("Redirecting to "+ data.url);
                                    location.href = data.url;
                                } else {
                                    setTimeout(function () {
                                        if(data.message) _t.err_msg = data.message;
                                        else  _t.err_msg = "Unexpected Error occurred!";
                                        id_loading_overlay.style.display = "none";
                                    }, 1000);
                                }
                            },
                            error: function(data) {
                                // console.log("Error");
                                // console.table(data);
                                setTimeout(function () {
                                    if(data.message) _t.err_msg = data.message;
                                    else  _t.err_msg = "Unexpected Error occurred!";
                                    id_loading_overlay.style.display = "none";
                                }, 1000);
                            }
                        });
                    },
                },
                created: function () {
                    let _t = this;
                    let zip_code = _t.$cookies.get(v_cookies_keys.zip_code);
                    if (!zip_code)
                        router.push({name: v_all_routes_name.zip});

                    let cookie_own_input = _t.$cookies.get(v_cookies_keys.own_input);
                    if (!cookie_own_input)
                        router.push({name: v_all_routes_name.quote});
                }
            },
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