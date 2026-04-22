function [brdc,err] = read_brdv2(fname)
% This function reads navigation message from the RINEX 2.xx file
% Input  : fname    - the name of navigation file [char][ ]
% Output : brd      - coefficients taken from the 
%                     navigation message [structure]
%          brd.gps  - broadcast parameters for GPS system 
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
    % RINEX 2 version includes only GPS satellites
    brdc.gps = NaN(384,39);
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
            case 'PGM / RUN BY / DATE'
                % Name of program creating current file [3A20]
                binf.agency.soft = strtrim(line( 1:20));
                % Name of agency creating current file
                binf.agency.name = strtrim(line(21:40));
                % Date and time of file creation (format:yyyymmdd hhmmss zone - zone: 3-4 char. code for time zone)
                binf.agency.date = strtrim(line(41:60));
            case 'ION ALPHA'
                % Ionosphere parameters A0-A3 of almanac [2X,4D12.4]
                tline = strrep(line(1:60),'D','e');
                ialfa = sscanf(tline,'%e')';

                if ~isempty(ialfa)
                    binf.ialfa = ialfa;
                end
            case 'ION BETA'
                % Ionosphere parameters B0-B3 of almanac [2X,4D12.4]
                tline = strrep(line(1:60),'D','e');
                ibeta = sscanf(tline,'%e')';
                if ~isempty(ibeta)
                    binf.ibeta = ibeta;
                end
            case 'DELTA-UTC: A0,A1,T,W'
                % Almanac parameters to compute time in UTC [3X,2D19.12, 2I9]
                tline = strrep(line(1:60),'D','e');
                binf.dutc = sscanf(tline,'%e')';
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
    gep = 0;
    while ~feof(fid)
        line = fgetl(fid);
        if ~isempty(sscanf(line(1:2),'%d'))
            gep = gep + 1;
            tline = strrep(line,'D','e');
            asd = sscanf(tline(1:end),'%e')';
            % first line
            brdc.gps(gep,1:10) = asd;
            % other lines
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
            % time information in second of day
            % brdc.gps(gep,  39) = asd(5)*3600 + asd(6)*60 + asd(7);

            % time of clock
            y = brdc.gps(gep,2);
            if y<2000
                y = y + 2000;
            end
            brdc.gps(gep,39) = modjuldat(y,brdc.gps(gep,3),brdc.gps(gep,4),...
                brdc.gps(gep,5),brdc.gps(gep,6),brdc.gps(gep,7));
            % time of ephemeris
            brdc.gps(gep,40) = 44244 + brdc.gps(gep,29)*7 + brdc.gps(gep,19)/86400;
            % transmission time
            brdc.gps(gep,41) = 44244 + brdc.gps(gep,29)*7 + brdc.gps(gep,35)/86400;
        end
    end
    
catch ME
    err.cod = 2;
    msg{1} = ['Hata mesajı:',ME.message]; 
    msg{2} = ['"',ME.stack(1).name,'" fonksiyonunun ', num2str(ME.stack(1).line),'. satırında hata!'];
    err.msg = msg;
    brdc=[];
    return
end

end