/********** Document Ready Function ************/
$(document).ready(function(){
    msObject_.DOMready();
    msObject_.eventBinder();
    msObject_.winHeight('.msWinHeight');

    //same height for all div
    if ($(window).outerWidth() > 990){
    	MakeSameHeight($('.nahq-plan-same-height .plan-content'));
    	MakeSameHeight($('section.plan-details-variations.common-section .col-md-4'));
    }


    function MakeSameHeight ( param )
    {
	    var maxHeight = 0;
    	param.each(function () {
    		var _t = $(this);
		    if (maxHeight < _t.outerHeight())
		    	maxHeight = _t.outerHeight();
	    });
    	param.height(maxHeight);
    }


	$('.quote-filter-title').append('<span class="visible-xs-inline-block" style="position: absolute;right: 5px;color: #5398f3;"><i class="fa fa-caret-down"></i></span>');
    //check initially
	Filtering_in_Mobile();
});

//filtering
var _filter_plan = $('#filtering_mobile');
var scrollLen = 213;
var _sidebar_col = $('.sidebar-col-holder');
var _all_plans = $('#month_plan_list');
var _sub_filter_name = $('h3.quote-filter-title');
var _sub_filters = $('.custom-check-holder>ul');

function Filtering_in_Mobile() {
	if ($(window).width() < 767)
	{
		$(window).scroll(function () {
			if ($(window).scrollTop() > scrollLen) {
				_filter_plan.addClass('fixed-at-top');
				_all_plans.css('margin-top', 64);   //for not making the button jumping (64 is the spacing for the filter button)
			}
			else {
				_filter_plan.removeClass('fixed-at-top');
				_all_plans.css('margin-top', 0);
			}
		});

		//button filtering
		_sub_filter_name.unbind();  //unbind click event because the function called twice if the screen comes smaller from big
		_sub_filter_name.click(function (e) {
		    e.preventDefault();
		    $('.custom-check-holder>ul').slideUp(); //slide all others

		    var _next = $(this).next('ul');
		    if (_next.is(':visible'))
			    _next.slideUp();
		    else
			    _next.slideDown();

		});
	}
	else
	{
		Reset_filtering();
	}
}

function Reset_filtering() { //reset the filtering option if not in mobile
	_filter_plan.removeClass('fixed-at-top');
	_all_plans.css('margin-top', 0);
	_sidebar_col.show();
	_sub_filter_name.unbind();
	_sub_filters.show();
}

//Main filter button
$('#filter-btn-wrapper').click(function (e) {
	e.preventDefault();
	$('.sidebar-col-holder').slideToggle();
});



/********** Window load complete *************/
$(window).load(function(){
    msObject_.winLoad();


});

$(window).resize(function () {
	Filtering_in_Mobile();
});

/************** Window resize ***************/
$(window).resize(debouncer(function(){
    msObject_.winHeight('.msWinHeight');
}));
