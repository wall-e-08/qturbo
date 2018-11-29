'use strict';   // this will prevent assigning variables without declaring!

const ppp = {
    template: `
        <div>
            Parent !!<br>
            <router-view></router-view>
        </div>`
};  // need router view for child element!

const cccc = {
    template: `
        <div>
            Childreeeeeeen !!!
        </div>`
};

const router = new VueRouter({
    routes: [{
        path: '/fff',
        component: ppp,
        name: 'parent',
        children: [{
            path: 'ggg',
            component: cccc,
            name: 'child',
        },]
    },]
});

// this should be initialized at last.
// this is bootstrap-vue
new Vue({
    delimiters: ['[[', ']]'],
    router,
}).$mount('#bootstrap-vue');
