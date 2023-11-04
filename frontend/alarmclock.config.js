/**
 * Alarmclock config component
 * Handle alarmclock application configuration
 * If your application doesn't need configuration page, delete this file and its references into desc.json
 */
angular
.module('Cleep')
.directive('alarmclockConfigComponent', ['$rootScope', 'cleepService', 'toastService', 'alarmclockService', '$location', '$filter',
function($rootScope, cleepService, toastService, alarmclockService, $location, $filter) {

    var alarmclockConfigController = function($scope) {
        var self = this;
        self.defaultTime = new Date(1970, 0, 1, 8, 0);
        self.config = {};
        self.devices = [];
        self.devicesList = [];
        self.nonWorkingDays = false;
        self.time = self.defaultTime;
        self.timeout = 15;
        self.volume = 50;
        self.days = [
            { label: 'Monday', value: 'mon' },
            { label: 'Tuesday', value: 'tue' },
            { label: 'Wednesday', value: 'wed' },
            { label: 'Thursday', value: 'thu' },
            { label: 'Friday', value: 'fri' },
            { label: 'Saturday', value: 'sat' },
            { label: 'Sunday', value: 'sun' },
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

            alarmclockService.addAlarm(self.time.getHours(), self.time.getMinutes(), self.timeout, days, self.nonWorkingDays, self.volume, self.playlistRepeat, self.playlistShuffle)
                .then(resp => {
                    toastService.success('Alarm added');
                    cleepService.reloadDevices();
                    self.clearForm();
                });
        };

        self.clearForm = function() {
            self.selectedDays.splice(0, self.selectedDays.length);
            self.nonWorkingDays = false;
            self.time = self.defaultTime;
            self.timeout = 15;
            self.volume = 50;
            self.playlistRepeat = true;
            self.playlistShuffle = false;
        };

        self.removeAlarm = function(device) {
            self.__removeAlarm(device.uuid, true);
        };

        self.__removeAlarm = function(alarmUuid, showToast) {
            alarmclockService.removeAlarm(alarmUuid)
                .then(resp => {
                    if (showToast) {
                        toastService.success('Alarm deleted');
                    }
                    cleepService.reloadDevices();
                });
        };

        self.editAlarm = function(device) {
            self.duplicateAlarm(device);
            self.__removeAlarm(device.uuid, false);
        };

        self.duplicateAlarm = function(device) {
            self.selectedDays.splice(0, self.selectedDays.length);
            for (const [day, enabled] of Object.entries(device.days)) {
                if (enabled) {
                    self.selectedDays.push(day);
                }
            }
            self.nonWorkingDays = device.nonWorkingDays;
            self.time = new Date(1970, 0, 1, device.time.hour, device.time.minute);
            self.timeout = device.timeout;
            self.volume = device.volume;
            self.playlistRepeat = device.repeat;
            self.playlistShuffle = device.shuffle;
        };

        self.toggleAlarm = function(device) {
            alarmclockService.toggleAlarm(device.uuid)
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

        $rootScope.$watch(
            () => cleepService.modules['alarmclock'].config,
            (newConfig) => {
                if(newConfig && Object.keys(newConfig).length) {
                    cleepService.syncVar(self.config, newConfig);
                }
            },
        );

        $rootScope.$watchCollection(
            () => cleepService.devices,
            (newDevices) => {
                if (!newDevices) {
                    return;
                }

                const devices = cleepService.getModuleDevices('alarmclock');
                cleepService.syncVar(self.devices, devices);

                self.devicesList.splice(0, self.devicesList.length);
                for (const [index, device] of devices.entries()) {
                    const time = $filter('padzero')(device.time.hour) + ':' + $filter('padzero')(device.time.minute);
                    const repeat = device.repeat ? 'on' : 'off';
                    const shuffle = device.shuffle ? 'on' : 'off';
                    const nonWorkingDays = device.nonWorkingDays ? 'enabled' : 'disabled';

                    self.devicesList.push({
                        icon: device.enabled ? 'alarm-check' : 'alarm-off',
                        iconClass: device.enabled ? '' : 'md-accent',
                        title: 'Start at ' + time + ' on ' + $filter('hrDays')(device.days),
                        subtitle: 'Timeout after ' + device.timeout + ' mins, volume at ' + device.volume  + '%, repeat ' + repeat + ', shuffle ' + shuffle + ', ' + nonWorkingDays + ' on non-working days',
                        clicks: [
                            {
                                icon: 'pencil',
                                tooltip: 'Edit alarm',
                                click: self.editAlarm,
                                meta: { device },
                            },
                            {
                                icon: 'content-duplicate',
                                tooltip: 'Copy alarm',
                                click: self.duplicateAlarm,
                                meta: { device },
                            },
                            {
                                icon: device.enabled ? 'alarm-off' : 'alarm-check',
                                tooltip: device.enabled ? 'Turn off alarm' : 'Turn on alarm',
                                click: self.toggleAlarm,
                                meta: { device },
                            },
                            {
                                icon: 'delete',
                                tooltip: 'Delete alarm',
                                click: self.removeAlarm,
                                class: 'md-accent',
                                meta: { device },
                            },
                        ],
                    });
                }
            },
        );
    };

    return {
        templateUrl: 'alarmclock.config.html',
        replace: true,
        scope: true,
        controller: alarmclockConfigController,
        controllerAs: '$ctrl',
    };
}]);
