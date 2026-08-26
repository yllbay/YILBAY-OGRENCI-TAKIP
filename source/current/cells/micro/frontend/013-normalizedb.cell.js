

function normalizeDb(x){
 x.assignments??=[];
 x.weeklyPlans??={};
 x.aiPlans??={};
 x.videoSuggestions??={};
 x.homeworkAnalyses??=[];
 x.repeatSignals??=[];
 x.threshold??=70;
 return x
}
