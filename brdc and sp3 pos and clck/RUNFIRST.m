clc, clear all
% comparison of the coordinates obtained from precise and broadcast ephemeris
% 
% file names
f_sp3 = 'IGS0OPSFIN_20250300000_01D_15M_ORB.SP3';
f_brd = 'BRDC00IGS_R_20250300000_01D_MN.rnx';
f_atx = 'igs20.atx';

% read the files
[sp3] = read_sp3(f_sp3);
[brdc,~] = read_brd(f_brd);
[satx,~] = read_satx(f_atx);

% time definition
tim.year  =   2025;
tim.mont  =      1;
tim.day   =     30;
tim.dt    = 51.184; % constant time difference between TT and GPS time
t = 0 : 30 : 82800;  

for prn = 1 : 32 % satellite PRN number
    for iep = 1 : length(t)
        
        disp([num2str(prn),' - ',num2str(iep)]);
        tim.sec   = t(iep);    % second of day  
        [~,mjd]   = cal2jul(tim.year,tim.mont,tim.day,(tim.sec));
        [~,mjdtt] = cal2jul(tim.year,tim.mont,tim.day,(tim.sec+tim.dt));
        tim.mjd   = mjd;
        tim.mjdtt = mjdtt;

        % compute the satellite coordinates and clock correction from precise
        % ephemeris
        [ssp3] = calc_sp3(sp3,satx,prn,tim);

        % compute the satellite coordinates and clock correction from broadcast
        % ephemeris
        [sbrd] = calc_brd(brdc,prn,tim);

        igssat(prn).epsec(iep) = t(iep);
        igssat(prn).epmjd(iep) = mjd;
        igssat(prn).ssp3(iep,1:4) = ssp3;
        igssat(prn).sbrd(iep,1:4) = sbrd;
    end
end

c    = 299792458; % light velocity in vacuum [m/s] 
datestr = [num2str(tim.year),'/',num2str(tim.mont),'/',num2str(tim.day)];

figure(1)
subplot(2,1,1)
hold on, box on
title("satellite ECEF coordinate differences [broadcast-sp3]")
plot(igssat(1).epsec/3600,igssat(1).sbrd(:,1:3)-igssat(1).ssp3(:,1:3),'.')
legend(["{\Delta}X";"{\Delta}Y";"{\Delta}Z"])
xlabel(['hours of the day, ',datestr ])
ylabel('[m]')

subplot(2,1,2)
hold on, box on
title("satellite clock error differences [broadcast-sp3]")
plot(igssat(1).epsec/3600,(igssat(1).sbrd(:,4:4)-igssat(1).ssp3(:,4:4))*c,'.')
xlabel(['hours of the day, ',datestr ])
ylabel('[m]')

save igssat igssat