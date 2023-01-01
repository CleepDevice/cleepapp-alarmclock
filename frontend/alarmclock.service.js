/**
 * Alarmclock service.
 * Handle alarmclock application requests.
 * Service is the place to store your application content (it is a singleton) and
 * to provide your application functions.
 */
angular
.module('Cleep')
.filter('hrDays', function() {
    return function(days) {
        if (!days) return ''; 
        const selectedDays =[];
        if (days['mon']) selectedDays.push('mon');
        if (days['tue']) selectedDays.push('tue');
        if (days['wed']) selectedDays.push('wed');
        if (days['thu']) selectedDays.push('thu');
        if (days['fri']) selectedDays.push('fri');
        if (days['sat']) selectedDays.push('sat');
        if (days['sun']) selectedDays.push('sun');
        return selectedDays.join(', ') || 'No day selected';
    };  
})
.service('alarmclockService', ['$rootScope', 'rpcService',
function($rootScope, rpcService) {
    var self = this;

    self.addAlarm = function(hour, minute, timeout, days, nonWorkingDays, volume, repeat, shuffle) {
        return rpcService.sendCommand('add_alarm', 'alarmclock', {
            alarm_time: { hour, minute },
            timeout,
            days,
            non_working_days: nonWorkingDays,
            volume,
            repeat,
            shuffle,
        });
    };

    self.removeAlarm = function(alarmUuid) {
        return rpcService.sendCommand('remove_alarm', 'alarmclock', {
            alarm_uuid: alarmUuid,
        });
    };

    self.toggleAlarm = function(alarmUuid) {
        return rpcService.sendCommand('toggle_alarm', 'alarmclock', {
            alarm_uuid: alarmUuid,
        });
    };
}]);
