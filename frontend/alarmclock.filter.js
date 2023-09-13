angular
.module('Cleep')
.filter('alarmclockDays', function() {
    return function(days) {
        if (!days) return ''; 
        const selectedDays = [];
        if (days['mon']) selectedDays.push('Mo');
        if (days['tue']) selectedDays.push('Tu');
        if (days['wed']) selectedDays.push('We');
        if (days['thu']) selectedDays.push('Th');
        if (days['fri']) selectedDays.push('Fr');
        if (days['sat']) selectedDays.push('Sa');
        if (days['sun']) selectedDays.push('Su');
        return selectedDays.join(',') || 'No day selected';
    };
});

