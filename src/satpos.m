function [sat_p,sat_v] = satpos(t,sow,eph,satnum)

% This function calculates GPS Satellite position and velocity (ECEF) at
% time t the navigation ephemeris as input
%
% Input :  t      - time of signal emission in MJD
%          sow    - time of the signal emission in seconds of week
%          eph    - structure array where the broadcast nagivation message is stored
% 
% Output : sat_p  - satellite position in ECEF [m] 
%          sat_v  - satellite velocity in ECEF [m]

% Earth's universal gravitational constant [m/s^2]
GM = 3986004.418 * 10^8; % [m³/s²];  
% Earth's rotation rate [rad/s]
we_dot = 7.2921151467e-5; % WGS84 value for Earth angular velocity (rad/s)

ind = find(eph(1,:)==satnum);
jd = gps2jd(eph(27,ind),eph(18,ind));
epoch = jd2mjd(jd);
indep = find(epoch<=t);
nind = ind(1)-1+indep(end);

%  Units are either [second], [meter] or [radian]
%  Assigning the local variables to eph
svprn   =  eph(01,nind);     % satellite number
af2     =  eph(02,nind);     % [s/s^2], satellite clock drift rate 
M0      =  eph(03,nind);     % mean anomaly  [rad]
roota   =  eph(04,nind);     % square-root of semi-major axis [sqrt(m)]
deltan  =  eph(05,nind);     % mean motion value [rad/s]
ecc     =  eph(06,nind);     % eccentricity
omega   =  eph(07,nind);     % omega [rad]
cuc     =  eph(08,nind);     % amplitude of the .... [rad]
cus     =  eph(09,nind);     % amplitude of the .... [rad]   
crc     =  eph(10,nind);     % amplitude of the .... [m]
crs     =  eph(11,nind);     % amplitude of the .... [m]
i0      =  eph(12,nind);     % inclincation angle at reference time [rad]
idot    =  eph(13,nind);     % rate of inclination angle [rad/s]
cic     =  eph(14,nind);     % amplitude of the .... [rad]
cis     =  eph(15,nind);     % amplitude of the .... [rad]
Omega0  =  eph(16,nind);     % longitude of the ascending node [rad]
Omegadot=  eph(17,nind);     % rate of the right ascension [rad/s]
toe     =  eph(18,nind);     % [sow], time of ephemeris 
af0     =  eph(19,nind);     % [s], sv clock bias 
af1     =  eph(20,nind);     % [s/s], sv clock drift 
toc     =  eph(21,nind);     % time of clock [s] seconds of gps-week
tgd     =  eph(22,nind);     % time of group delay [s] time group delay 
svhealth = eph(23,nind);     % bits 17-22 w 3 sf 1
IODE    = eph(24,nind);      % Issue of Data Ephemeris
IODC    = eph(25,nind);      % Issue of Data Clocks
codes   = eph(26,nind);      % codes on L2 channel
weekno  = eph(27,nind);      % gps-week, continuos number
accuracy = eph(28,nind);     % [m] sat in space accuracy

% Start coordinate calculation
A  = roota^2;         	% semi-major axis
tk = check_t(sow-toe);  % time of ephemeris, repair over/underflow
n0 = sqrt(GM/A^3);      % mean angular velocity
n  = n0+deltan;       	% corrected mean angular velocity
M = M0+n*tk;            % mean anomaly
M = rem(M+2*pi,2*pi);

E0 = M;
while 1
    E = M + ecc*sin(E0);
    dE = abs(E - E0);
    if dE<1*10^-15
        break
    else
        E0 = E;
    end
end
E = rem(E+2*pi,2*pi);   % eccentric anomaly

v = atan2(sqrt(1-ecc^2)*sin(E), cos(E)-ecc); % true anomaly
u0 = v + omega;           % argument of latitude
u0 = rem(u0,2*pi);

u = u0               + cuc*cos(2*u0)+cus*sin(2*u0); % corrected argument of latitude
r = A*(1-ecc*cos(E)) + crc*cos(2*u0)+crs*sin(2*u0); % corrected radius
i = i0+idot*tk       + cic*cos(2*u0)+cis*sin(2*u0); % corrected inclination
Omega = Omega0 + (Omegadot - we_dot)*tk - we_dot*toe; 	% corrected longitude of ascending node
Omega = rem(Omega+2*pi,2*pi);

% (1) Orbital plane position
x1 = cos(u)*r;
y1 = sin(u)*r;

% (2) ECEF position
sat_p(1,1) = x1*cos(Omega) - y1*cos(i)*sin(Omega);
sat_p(2,1) = x1*sin(Omega) + y1*cos(i)*cos(Omega);
sat_p(3,1) = y1*sin(i);

e_help = 1/(1-ecc*cos(E));
dot_v  = sqrt((1 + ecc)/(1 - ecc)) / cos(E/2)/cos(E/2) / (1 + tan(v/2)^2) * e_help * n;
dot_u  = dot_v + (-cuc*sin(2*u0) + cus*cos(2*u0))*2*dot_v;
dot_om = Omegadot - we_dot;
dot_i  = idot + (-cic*sin(2*u0) + cis*cos(2*u0))*2*dot_v;
dot_r  = A*ecc*sin(E) * e_help * n + (-crc*sin(2*u0) + crs*cos(2*u0))*2*dot_v;

% (1a) Velocity in orbital plane
dot_x1 = dot_r*cos(u) - r*sin(u)*dot_u;
dot_y1 = dot_r*sin(u) + r*cos(u)*dot_u;

% (2a) ECEF velocity
sat_v(1,1) = cos(Omega)*dot_x1 - cos(i)*sin(Omega)*dot_y1 - x1*sin(Omega)*dot_om - y1*cos(i)*cos(Omega)*dot_om + y1*sin(i)*sin(Omega)*dot_i;        
sat_v(2,1) = sin(Omega)*dot_x1 + cos(i)*cos(Omega)*dot_y1 + x1*cos(Omega)*dot_om - y1*cos(i)*sin(Omega)*dot_om - y1*sin(i)*cos(Omega)*dot_i;
sat_v(3,1) = sin(i)    *dot_y1  + y1*cos(i)*dot_i;

end