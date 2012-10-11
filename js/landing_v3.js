$(window).load(function(){
	//track loadtime
	var endTime = (new Date()).getTime();
    var millisecondsLoading = endTime - startTime;
	mixpanel.track("Levr V3 Landing Page Loaded",{"Load Time":millisecondsLoading})
	
	mixpanel.track_links("#buttonbeta", "Beta button clicked");
	
	mixpanel.track_links("#buttonRadius", "Radi.us button clicked");
	
	mixpanel.track_links("#buttonMerchants", "Merchants button clicked");

	
})