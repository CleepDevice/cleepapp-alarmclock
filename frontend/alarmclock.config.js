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
        self.nonWorkingDays = false;
        self.hour = 8;
        self.minute = 0;
        self.timeout = 15;
        self.volume = 50;
        self.days = [
            { label: 'Monday', val: 'mon' },
            { label: 'Tuesday', val: 'tue' },
            { label: 'Wednesday', val: 'wed' },
            { label: 'Thursday', val: 'thu' },
            { label: 'Friday', val: 'fri' },
            { label: 'Saturday', val: 'sat' },
            { label: 'Sunday', val: 'sun' },
        ];
        self.selectedDays = [];
        self.playlistRepeat = true;
        self.playlistShuffle = false;

        self.$onInit = function() {
            cleepService.getModuleConfig('alarmclock');
            cleepService.reloadDevices();
        };

        self.addAlarm = function() {
            var days = {
                mon: self.selectedDays.indexOf('mon') !== -1,
                tue: self.selectedDays.indexOf('tue') !== -1,
                wed: self.selectedDays.indexOf('wed') !== -1,
                thu: self.selectedDays.indexOf('thu') !== -1,
                fri: self.selectedDays.indexOf('fri') !== -1,
                sat: self.selectedDays.indexOf('sat') !== -1,
                sun: self.selectedDays.indexOf('sun') !== -1,
            };
            alarmclockService.addAlarm(self.hour, self.minute, self.timeout, days, self.nonWorkingDays, self.volume, self.playlistRepeat, self.playlistShuffle)
                .then(resp => {
                    toastService.success('Alarm added');
                    cleepService.reloadDevices();
                    self.clearForm();
                });
        };

        self.clearForm = function() {
            while (self.selectedDays.length > 0) self.selectedDays.pop();
            self.nonWorkingDays = false;
            self.hour = 8;
            self.minute = 0;
            self.timeout = 15;
            self.volume = 50;
            self.playlistRepeat = true;
            self.playlistShuffle = false;
        };

        self.removeAlarm = function(alarmUuid, showToast) {
            alarmclockService.removeAlarm(alarmUuid)
                .then(resp => {
                    if (showToast === undefined || showToast === true) {
                        toastService.success('Alarm deleted');
                    }
                    cleepService.reloadDevices();
                });
        };

        self.editAlarm = function(alarm) {
            self.duplicateAlarm(alarm);
            self.removeAlarm(alarm.uuid, false);
        };

        self.duplicateAlarm = function(alarm) {
            while (self.selectedDays.length > 0) self.selectedDays.pop();
            for (const [day, enabled] of Object.entries(alarm.days)) {
                if (enabled) {
                    self.selectedDays.push(day);
                }
            }
            self.nonWorkingDays = alarm.nonWorkingDays;
            self.hour = alarm.time.hour;
            self.minute = alarm.time.minute;
            self.timeout = alarm.timeout;
            self.volume = alarm.volume;
            self.playlistRepeat = alarm.repeat;
            self.playlistShuffle = alarm.shuffle;
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
            if (self.selectedDays.length) {
                while (self.selectedDays.length > 0) self.selectedDays.pop();
            } else {
                self.days.forEach(day => self.selectedDays.push(day.val));
            }
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
