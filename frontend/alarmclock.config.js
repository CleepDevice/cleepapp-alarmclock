/**
 * Alarmclock config component
 * Handle alarmclock application configuration
 * If your application doesn't need configuration page, delete this file and its references into desc.json
 */
angular
.module('Cleep')
.directive('alarmclockConfigComponent', ['$rootScope', 'cleepService', 'toastService', 'alarmclockService', '$location',
function($rootScope, cleepService, toastService, alarmclockService, $location) {

    var alarmclockConfigController = function($scope) {
        var self = this;
        self.config = {};
        self.devices = [];
        self.daysMapping = {0: 'mon', 1: 'tue', 2: 'wed', 3: 'thu', 4: 'fri', 5: 'sat', 6: 'sun'};
        // monday is 0 (first item), sunday is 6
        self.days = [false, false, false, false, false, false, false];
        self.nonWorkingDays = false;
        self.hour = 8;
        self.minute = 0;
        self.timeout = 15;
        self.volume = 50;

        self.$onInit = function() {
            cleepService.getModuleConfig('alarmclock');
            cleepService.reloadDevices();
        };

        self.addAlarm = function() {
            var days = {
                mon: self.days[0],
                tue: self.days[1],
                wed: self.days[2],
                thu: self.days[3],
                fri: self.days[4],
                sat: self.days[5],
                sun: self.days[6],
            };
            alarmclockService.addAlarm(self.hour, self.minute, self.timeout, days, self.nonWorkingDays, self.volume)
                .then(resp => {
                    toastService.success('Alarm added');
                    cleepService.reloadDevices();
                    self.clearForm();
                });
        };

        self.clearForm = function() {
            self.days.forEach((day, index) => self.days[index] = false);
            self.nonWorkingDays = false;
            self.hour = 8;
            self.minute = 0;
            self.timeout = 15;
            self.volume = 50;
        };

        self.removeAlarm = function(alarmUuid) {
            alarmclockService.removeAlarm(alarmUuid)
                .then(resp => {
                    toastService.success('Alarm deleted');
                    cleepService.reloadDevices();
                });
        };

        self.duplicateAlarm = function(alarm) {
            self.days.forEach((day, index) => self.days[index] = alarm.days[self.daysMapping[index]]);
            self.nonWorkingDays = alarm.nonWorkingDays;
            self.hour = alarm.time.hour;
            self.minute = alarm.time.minute;
            self.timeout = alarm.timeout;
            self.volume = alarm.volume;
        };

        self.toggleAlarm = function(alarmUuid) {
            alarmclockService.toggleAlarm(alarmUuid)
                .then(resp => {
                    var message = resp.data ? 'Alarm enabled' : 'Alarm disabled';
                    toastService.success(message);
                    cleepService.reloadDevices();
                });
        };

        self.toggleAllDays = function() {
            self.days.forEach((day, index) => self.days[index] = !self.days[index]);
        };

        $rootScope.$watch(function() {
            return cleepService.modules['alarmclock'].config;
        }, function(newConfig, oldConfig) {
            if(newConfig && Object.keys(newConfig).length) {
                cleepService.syncVar(self.config, newConfig);
            }
        });

        $rootScope.$watchCollection(function() {
            return cleepService.devices;
        }, function(newDevices, oldDevices) {
            if(newDevices && newDevices.length) {
                const devices = cleepService.getModuleDevices('alarmclock');
                cleepService.syncVar(self.devices, devices);
            }
        });
    };

    return {
        templateUrl: 'alarmclock.config.html',
        replace: true,
        scope: true,
        controller: alarmclockConfigController,
        controllerAs: 'alarmclockCtl',
    };
}]);
