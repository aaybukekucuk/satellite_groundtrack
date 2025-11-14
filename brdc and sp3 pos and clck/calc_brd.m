function [sbrd] = calc_brd(brdc,prn,tim)

brds = brdc.gps(brdc.gps(:,1)==prn,:);

% latest
bm = max(brds(brds(:,41)<tim.mjd,41));
brd = brds(brds(:,41)==bm,:);

trc = tim.mjd;

[pos] = orb_cal(brd,trc);

sbrd = horzcat(pos(1:3),pos(7));

end

function [pos] = orb_cal(brd,trc)
% brd : related broadcast parameters
% trc : time of reception (receiver)
% obs : the related code observation
% rec : receiver position

% constants
%c  = 299792458; % m/s velocity of light
mu = 3.986005*10^14; % m3/s2; % m3/s2
we = 7.2921151467*10^-5; % rad/s
%F  = (-2*sqrt(mu))/c^2;  % sec/sqrt(m)

TocMjd = brd(39); % time of clock (toc) in mjd
TOEmjd = brd(40); % time of ephemeris (toe) in mjd

% % first iteration
% % time from ephemeris reference epoch (toe) to signal emission time (first iteration)
% tk0 = round((trc - TOEmjd)*86400,5) - (obs./c); % round: (trc-TocMjd)*86400 should be integer seconds
% 
% a = brd(1,18)^2;              % m
% e = brd(1,16);
% nm = sqrt(mu/a^3) + brd(1,13); % corrected mean motion (rad/sec)        
% Mk = brd(1,14) + nm*tk0;        % mean anomaly for the first iteration (rad) 
% E0 = Mk;
% ni = 0;
% while 1
%     ni = ni + 1;
%     Eki = Mk + e*sin(E0); % eccentric anomaly (initial)
%     dE = abs(Eki - E0);
%     if dE<1*10^-15 || ni>15
%         break
%     else
%         E0 = Eki;
%     end
% end
% % relativistic clock correction (first iteration)
% Dtr0 = F*brd(1,16)*brd(1,18)*sin(Eki); %seconds
% 
% % time from clock reference epoch (toc) to signal emission time (first iteration)
% dt0 = round((trc - TocMjd)*86400,5) - (obs./c); % round: (trc-TocMjd)*86400 should be integer seconds
% 
% % clock correction at signal transmission time (first iteration)
% cd = brd(1,8) + (brd(1,9)*dt0) + (brd(1,10)*(dt0^2)) + Dtr0; %seconds

% final iteration
% corrected time from ephemeris reference epoch (toe) to signal emission time
tk = round((trc - TOEmjd)*86400,3);

a = brd(1,18)^2;              % m
e = brd(1,16);
nm = sqrt(mu/a^3) + brd(1,13); % corrected mean motion (rad/sec)
Mk = brd(1,14) + nm*tk;  % corrected mean anomaly
E0 = Mk;
ni = 0;
while 1
    ni = ni + 1;
    Ek = Mk + e*sin(E0); % corrected eccentric anomaly 
    dE = abs(Ek - E0);
    if dE<1*10^-15 || ni>15
        break
    else
        E0 = Ek;
    end
end
% corrected relativistic clock correction
%Dtr = F*brd(1,16)*brd(1,18)*sin(Ek); %seconds
% corrected time from clock reference epoch (toc) to signal emission time
dt = round((trc - TocMjd)*86400,3);
% clock correction (corrected)
clk = brd(1,8) + (brd(1,9)*dt) + (brd(1,10)*(dt^2));% + Dtr; %seconds

% true anamoly
vk = atan2((sqrt(1 - e^2)*sin(Ek)),(cos(Ek) - e));
fk = vk + brd(1,25); % argumant of latitude (rad)

cus = brd(1,17);% rad
cuc = brd(1,15);% rad
crs = brd(1,12);% m
crc = brd(1,24);% m
cis = brd(1,22);% rad
cic = brd(1,20);% rad

du = cus*sin(2*fk) + cuc*cos(2*fk);
dr = crs*sin(2*fk) + crc*cos(2*fk);
di = cis*sin(2*fk) + cic*cos(2*fk);

uk = fk + du;                % rad
rk = a*(1 - e*cos(Ek)) + dr; % m

i0 = brd(1,23);    % rad
id = brd(1,27);    % rad/s
ik = i0 + di + (id*tk);

xkp = rk*cos(uk); % in-plane x coordinate
ykp = rk*sin(uk); % in-plane y coordinate

omg0 = brd(1,21);
omgd = brd(1,26);
toe  = brd(1,19);
omg = omg0 + (omgd - we)*tk - (we*toe);

% Earth-fixed x, y, z coordinates
xk  = xkp*cos(omg) - ykp*cos(ik)*sin(omg);
yk  = xkp*sin(omg) + ykp*cos(ik)*cos(omg);
zk  = ykp*sin(ik);

% R  = [xk yk zk];
% 
% tf = norm(R - rec)./c;
% er_ang = rad2deg(tf*we);
% % satellite position correction for signal travel time
% rr = rot3d(R,er_ang,3);

% Velocity computations - IS-GPS-200, Table 20- IV  (sheet 3 of 4)
Ekdot = nm/(1-e*cos(Ek)); % Eccentric Anomaly Rate
vkdot = Ekdot*sqrt(1-e^2)/(1-e*cos(Ek)); % True Anomaly Rate
dikdot = id+2*vkdot*(cis*cos(2*fk)-cic*sin(2*fk)); % Corrected Inclination Angle Rate
ukdot = vkdot+2*vkdot*(cus*cos(2*fk)-cuc*sin(2*fk)); % Corrected Argument of Latitude Rate
rkdot = e*a*Ekdot*sin(Ek)+2*vkdot*(crs*cos(2*fk)-crc*sin(2*fk)); % Corrected Radius Rate
omgkdot = omgd-we; % Longitude of Ascending Node Rate

Vxp = rkdot*cos(uk)-rk*ukdot*sin(uk); % in-plane x velocity
Vyp = rkdot*sin(uk)+rk*ukdot*cos(uk); % in-plane y velocity

% Earth- Fixed x, y, z velocities (m/s)
Vx = -xkp*omgkdot*sin(omg) + Vxp*cos(omg) - Vyp*sin(omg)*cos(ik) - ykp*(omgkdot)*cos(omg)*cos(ik) - dikdot*sin(omg)*sin(ik);
Vy =  xkp*omgkdot*cos(omg) + Vxp*sin(omg) + Vyp*cos(omg)*cos(ik) - ykp*(omgkdot)*sin(omg)*cos(ik) - dikdot*cos(omg)*sin(ik);
Vz = Vyp*sin(ik) + ykp*dikdot*cos(ik);

pos = [xk yk zk Vx Vy Vz clk];

end