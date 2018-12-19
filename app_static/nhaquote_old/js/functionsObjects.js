/**** Global Objects for common uses ****/
// Main Objects
var msObject_ = {
    "DOMready" : function(){
        $('[data-toggle="popover"]').popover({trigger:'hover'});

    },
    "winLoad" : function(){

    },
    "winHeight" : function(selector){
        $(selector).css('min-height',$(window).height());
    },
    "eventBinder" : function(){
        // cacheing the document DOM inside variable
        var doc = jQuery(document);
        doc.on('click', '.msScrollTo', function() {
            var go_to = $(this).attr('href') || $(this).data('href') || '#';
            if($(go_to).length > 0){$('html, body').animate({scrollTop:$(go_to).position().top}, 1500);}
            return false;
        });
        doc.on('click', '#mobileNavToggle,.navclosebtn', function(e) {
            e.preventDefault();
            $('body').toggleClass('global-side-open');
        });
        doc.on('click', '.custom-drop-down', function(e) {
            e.preventDefault();
            $(this).parent().toggleClass('open');
            e.stopPropagation();
        });
        doc.on('click', '.sort-drop-down li a', function(e) {
            v = $(this);
            v.parent().addClass('selected').siblings().removeClass('selected');
            v.closest('.sort-by').removeClass('open').find('.drop-text').text(v.text());
            e.preventDefault();
            e.stopPropagation();
        });
    }
};

/**** Global Functions for common uses ****/
//debounce function when rezize windows
function debouncer( func , timeout ) {
    var timeoutID , timeout = timeout || 200;
    return function () {
        var scope = this , args = arguments;
        clearTimeout( timeoutID );
        timeoutID = setTimeout( function () {
            func.apply( scope , Array.prototype.slice.call( args ) );
        } , timeout );
    }
}