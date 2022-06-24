$(document).ready(function(){
    $('.collapse').on('show.bs.collapse', function () {
	$(this).parent().find(".fa").toggleClass('fa-caret-down fa-caret-up');
    });

    $('.collapse').on('hide.bs.collapse', function () {
	$(this).parent().find(".fa").toggleClass('fa-caret-up fa-caret-down');
    });
});
