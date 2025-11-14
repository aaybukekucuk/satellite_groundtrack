clc, clear all, close all

addpath('COMMON')

% Read navigation file
navfile = 'BRDC00IGS_R_20240600000_01D_MN.rnx';
[~, eph] = readnav(navfile);

% options related to the initial values for the RK4 integration
option.integstartdate = [2024 2 29 16 30 58]; % integration start epoch [year month day hour minute second]
option.integinterval = 5; % integration interval in seconds
option.integspan = 86400; % integration span in seconds.

% epoch of interest
year = option.integstartdate(1);
month = option.integstartdate(2);
day = option.integstartdate(3);
hour = option.integstartdate(4);
minute = option.integstartdate(5);
second = option.integstartdate(6);
tmjd = modjuldat(year,month,day,hour,minute,second);
t = tmjd : option.integinterval/86400 : tmjd + (option.integspan/86400);

julday = mjd2jd(t);
[~,sow] = gps_time(julday);

for isat = 1 : 32
        sat(isat).satnum = isat;
    for iep = 1 : length(t)
        [sat_p, sat_v] = satpos(t(iep),sow(iep),eph,sat(isat).satnum);
        sat(isat).ep(iep,:) = t(iep);
        sat(isat).p(iep,:) = sat_p; % m
        sat(isat).v(iep,:) = sat_v; % m/s      
    end   
   
    disp(['G',num2str(sat(isat).satnum)]);
    
    figure(isat)
    hold on
    set(gcf,'DefaultAxesfontname','arial');
    set(gcf,'DefaultAxesfontsize',8);
    set(gcf,'PaperType','A4');
    set(gcf,'PaperOrientation','landscape');
    set(gcf,'PaperUnits','centimeters');
    set(gcf,'PaperPosition',[0 0 20 10]);
    title(['satellite G',num2str(sat(isat).satnum)])
    plot(sat(isat).ep,sat(isat).p.*0.001,'.')
    box on, grid on
    legend('X_{BRD}','Y_{BRD}','Z_{BRD}')
    ylabel('KM') 
    xlabel('MJD')

end

save sat sat