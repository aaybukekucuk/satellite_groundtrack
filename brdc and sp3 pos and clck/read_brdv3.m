function [brdc,err] = read_brdv3(fname)
% This function reads navigation message from the RINEX 3.xx file
% Input  : fname    - the name of navigation file [char][ ]
% Output : brd      - coefficients taken from the
%                     navigation message [structure]
%          brd.gps,
%          glo, gal,
%          bds, sbs - broadcast parameters for each system
%                     (probably 12 epochs in a day x satellite number) [384] x
%                     all broadcast parameters in one row combined
%                     respectively [39]
%          brd.binf - information about the broadcast [structure]
%                     ialfa - alfa coefficients
%                     ibeta - beta coefficients
%                     dutc  - delta utc
%                     leap  - leap seconds

% Initials
err.cod = 0;
err.msg = cell(0);
brdc = struct;

try
    % open the file
    [fid,~] = fopen(fname);
    %% read the header part
    % pre-definition of the related matrix
    % RINEX 3 version includes all GNSS satellites
    brdc.gps = NaN(384,41);
    brdc.glo = NaN(312,39);
    brdc.gal = NaN(432,39);
    brdc.bds = NaN(732,39);
    brdc.sbs = NaN(432,39);
    binf     = struct;
    binf.ialfa = NaN(1,4);
    binf.ibeta = NaN(1,4);
    % read the header file line-by-line
    while 1
        line = fgetl(fid);
        tag = strtrim(line(61:end));
        % tags of the header part
        switch tag
            case 'RINEX VERSION / TYPE'
                % RINEX format version [F9.2,11X]
                if strcmp(sscanf(line(21),'%c'),'N')
                    binf.rinex.type = sscanf(line(21),'%c');
                else
                    err.cod = 2;
                    err.msg = {'İlgili dosya navigasyon dosyası değil.'};
                    return
                end
                % Satellite system [A1,19X]
                % G: GPS
                % R: GLONASS
                % E: Galileo
                % J: QZSS
                % C: BDS
                % I: NavIC/IRNSS
                % S: SBAS payload
                % M: Mixed
                binf.rinex.system = sscanf(line(41),'%c');

            case 'PGM / RUN BY / DATE'
                % Name of program creating current file [3A20]
                binf.agency.soft = strtrim(line( 1:20));
                % Name of agency creating current file
                binf.agency.name = strtrim(line(21:40));
                % Date and time of file creation (format:yyyymmdd hhmmss zone - zone: 3-4 char. code for time zone)
                binf.agency.date = strtrim(line(41:60));

            case 'IONOSPHERIC CORR'
                % Ionospheric correction parameters
                % Correction type:
                if strcmp(line(1:4),'GPSA')
                    % GPS alpha0 - alpha3
                    tline = strrep(line(5:60),'D','e');
                    ialfa = sscanf(tline,'%e')';
                    if ~isempty(ialfa)
                        binf.ialfa = ialfa;
                    end
                elseif strcmp(line(1:4),'GPSB')
                    % GPS beta0 - beta3
                    tline = strrep(line(5:60),'D','e');
                    ibeta = sscanf(tline,'%e')';
                    if ~isempty(ibeta)
                        binf.ibeta = ibeta;
                    end
                end
            case 'TIME SYSTEM CORR'
                % Difference between GNSS system time and UTC or other time systems
                if strcmp(line(1:4),'GPUT')
                    tline = strrep(line(5:60),'D','e');
                    binf.dutc = sscanf(tline,'%e')';
                end

            case 'LEAP SECONDS'
                % Delta time due to leap seconds [I6]
                binf.leap = sscanf(line(1:60),'%f');

            case 'END OF HEADER'
                break
        end
    end

    if any(isnan(binf.ialfa)) || any(isnan(binf.ibeta))
        err.cod = 1;
        err.msg = [err.msg, {'Navigasyon dosyasında Klobuchar iyonosfer katsayıları mevcut değil.'}];
    end

    brdc.binf = binf;

    %% read the navigation part
    gep = 0; rep = 0; eep = 0; cep = 0; sep = 0;
    while ~feof(fid)
        line = fgetl(fid);
        if ~isempty(sscanf(line(1),'%c'))
            tline = strrep(line,'D','e');
            if strcmp(tline(1),'G')
                gep = gep + 1;
                asd = sscanf(tline(2:end),'%e')';
                brdc.gps(gep,1:10) = asd;
                for i=1:7
                    line = fgetl(fid);
                    tline = strrep(line,'D','e');
                    s = 11 + (i-1)*4;
                    f = 10 + i*4;
                    ts = sscanf(tline,'%e')';
                    if length(ts)<4
                        brdc.gps(gep,s:s+length(ts)-1) = ts;
                    else
                        brdc.gps(gep,s:f) = ts;
                    end
                end
                % brdc.gps(gep,39) = asd(5)*3600 + asd(6)*60 + asd(7);
                % time of clock
                brdc.gps(gep,39) = modjuldat(brdc.gps(gep,2),brdc.gps(gep,3),brdc.gps(gep,4),...
                    brdc.gps(gep,5),brdc.gps(gep,6),brdc.gps(gep,7));
                % time of ephemeris
                brdc.gps(gep,40) = 44244 + brdc.gps(gep,29)*7 + brdc.gps(gep,19)/86400;
                % transmission time
                brdc.gps(gep,41) = 44244 + brdc.gps(gep,29)*7 + brdc.gps(gep,35)/86400;

            elseif strcmp(tline(1),'R')
                rep = rep + 1;
                asd = sscanf(tline(2:end),'%e')';
                % GLONASS is in UTC
                brdc.glo(rep,1:10) = asd;
                [~,mjd] = cal2jul(asd(2),asd(3),asd(4),0);
                [ls] = detr_leap(mjd);
                for i=1:3
                    line = fgetl(fid);
                    tline = strrep(line,'D','e');
                    s = 11 + (i-1)*4;
                    f = 10 + i*4;
                    ts = sscanf(tline,'%e')';
                    if length(ts)<4
                        brdc.glo(rep,s:s+length(ts)-1) = ts;
                    else
                        brdc.glo(rep,s:f) = ts;
                    end
                end
                % Calculation GPS time
                brdc.glo(rep,  39) = asd(5)*3600 + asd(6)*60 + asd(7) + (ls-19);

            elseif strcmp(tline(1),'E')
                eep = eep + 1;
                asd = sscanf(tline(2:end),'%e')';
                brdc.gal(eep,1:10) = asd;
                for i=1:7
                    line = fgetl(fid);
                    tline = strrep(line,'D','e');
                    s = 11 + (i-1)*4;
                    f = 10 + i*4;
                    ts = sscanf(tline,'%e')';
                    if length(ts)<4
                        brdc.gal(eep,s:s+length(ts)-1) = ts;
                    else
                        brdc.gal(eep,s:f) = ts;
                    end
                end
                brdc.gal(eep,  39) = asd(5)*3600 + asd(6)*60 + asd(7);

            elseif strcmp(tline(1),'C')
                cep = cep + 1;
                asd = sscanf(tline(2:end),'%e')';
                % BeiDou is in BDT
                brdc.bds(cep,1:10) = asd;

                for i=1:7
                    line = fgetl(fid);
                    tline = strrep(line,'D','e');
                    s = 11 + (i-1)*4;
                    f = 10 + i*4;
                    ts = sscanf(tline,'%e')';
                    if length(ts)<4
                        brdc.bds(cep,s:s+length(ts)-1) = ts;
                    else
                        brdc.bds(cep,s:f) = ts;
                    end
                end
                % Calculation GPS time
                brdc.bds(cep,  39) = asd(5)*3600 + asd(6)*60 + asd(7) + 14;

            elseif strcmp(tline(1),'S')
                sep = sep + 1;
                asd = sscanf(tline(2:end),'%e')';
                brdc.sbs(sep,1:10) = asd;
                for i=1:3
                    line = fgetl(fid);
                    tline = strrep(line,'D','e');
                    s = 11 + (i-1)*4;
                    f = 10 + i*4;
                    ts = sscanf(tline,'%e')';
                    if length(ts)<4
                        brdc.sbs(sep,s:s+length(ts)-1) = ts;
                    else
                        brdc.sbs(sep,s:f) = ts;
                    end
                end
                brdc.sbs(sep,  39) = asd(5)*3600 + asd(6)*60 + asd(7);

            end
        end
    end
catch ME
    err.cod = 2;
    msg{1} = ['Hata mesajı:',ME.message];
    msg{2} = ['"',ME.stack(1).name,'" fonksiyonunun ', num2str(ME.stack(1).line),'. satırında hata!'];
    err.msg = msg;
    brdc = [];
    return
end

end