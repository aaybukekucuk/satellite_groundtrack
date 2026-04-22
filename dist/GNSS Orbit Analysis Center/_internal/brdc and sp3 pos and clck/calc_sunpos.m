function [s_pos] = calc_sunpos(mjd)

AU  = 149597870700;                                                   % met
d2r = pi/180;
fday = mjd - floor(mjd);
JDN  = mjd - 15019.5;

v1   = mod((279.696678 + 0.9856473354*JDN),360);                      % deg
gstr = mod((279.690983 + 0.9856473354*JDN + 360*fday + 180),360);     % deg
g    = (mod((358.475845 + 0.9856002670*JDN),360))*d2r;                % rad

slong = v1 + (1.91946 - 0.004789*JDN/36525)*sin(g)...
      + 0.020094*sin(2*g);                                            % deg
obliq = (23.45229 - 0.0130125*JDN/36525)*d2r;                         % rad

slp  = (slong - 0.005686)*d2r;                                        % rad
snd  = sin(obliq)*sin(slp);
csd  = sqrt(1 - snd^2);
sdec = atan2d(snd,csd);                                               % deg

sra = 180 - atan2d((snd/csd/tan(obliq)),(-cos(slp)/csd));             % deg

s_pos = [(cosd(sdec)*cosd(sra)*AU);...
         (cosd(sdec)*sind(sra)*AU);...
         (sind(sdec)*AU)];

s_pos = rotation(s_pos,gstr,3);                                       % met

end

function [out] = rotation(position,angle,axis)

narginchk(3,3)

if numel(position) ~= 3
     error('Matrix dimension shold be 3xN or Nx3.')
end


if numel(angle) ~= 1 || numel(axis) ~= 1
    error('Angle and axis should be scalar.')
end


switch axis
    case 1
        rot = [1 0 0; 0 cosd(angle) sind(angle); 0 -sind(angle) cosd(angle)];
    case 2
        rot = [cosd(angle) 0 -sind(angle); 0 1 0; sind(angle) 0 cosd(angle)];
    case 3 
        rot = [cosd(angle) sind(angle) 0; -sind(angle) cosd(angle) 0; 0 0 1];
end


[r,~] = size(position);

switch r
    case 1
        xout = rot*(position');
    case 3
        xout = rot*(position);
end

out = xout';
nargoutchk(1,1)
end