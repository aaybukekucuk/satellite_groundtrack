function [satx,err] = read_satx(fname)
% This function reads the satellite antenna phase center offsets and
% variations from ANTEX file
% Input  : fname - the name of ANTEX file [char][ ]
% Output : satx  - the satellite antenna phase center offsets and variations [structure]

% Initials
err.cod = 0;
err.msg = cell(0);
satx = struct;

satx.gps.daz = zeros(32,4);
satx.gps.neu = zeros(32,3,2);
satx.gps.nad = cell(32,2);
satx.gps.adp = cell(32,2);

try
    [fid,~] = fopen(fname);

    linenum = 0;
    while ~feof(fid)
        tline = fgetl(fid); linenum = linenum + 1;
        tag   = strtrim(tline(61:end));
        if strcmp(tag,'START OF ANTENNA')
            tline = fgetl(fid); linenum = linenum + 1;
            tag   = strtrim(tline(61:end));

            if strcmp(tag,'TYPE / SERIAL NO') && strcmp(tline(21),'G')
                sno = sscanf(tline(22:23),'%d');
                if sno>size(satx.gps.neu,1)
                    continue
                end
                
                while ~strcmp(tag,'END OF ANTENNA')
                    tline = fgetl(fid); linenum = linenum + 1;
                    tag   = strtrim(tline(61:end));
    
                    if strcmp(tag,'DAZI')
                        dazi = sscanf(tline(3:8),'%f');
                        satx.gps.daz(sno,1) = dazi;
                    end
                    if strcmp(tag,'ZEN1 / ZEN2 / DZEN')
                        dzen = sscanf(tline(3:20),'%f');
                        satx.gps.daz(sno,2:4) = dzen';
                        nzen = (dzen(2)-dzen(1))/dzen(3) + 1;
                    end
                    if strcmp(tag,'START OF FREQUENCY') && strcmp(tline(4:6),'G01')
                        fno = 1;
                        tline = fgetl(fid); linenum = linenum + 1;
                        tag   = strtrim(tline(61:end));
                        if strcmp(tag,'NORTH / EAST / UP')
                            satx.gps.neu(sno,:,fno) = sscanf(tline,'%f',[1,3]);
                            tline = fgetl(fid); linenum = linenum + 1;
                            satx.gps.nad{sno,fno} = sscanf(tline(9:end),'%f',[1,nzen]);
                            if dazi~=0
                                nn = 360/dazi + 1;
                                adp = NaN(nn,nzen+1);
                                for i=1:nn
                                    tline = fgetl(fid);
                                    linenum = linenum + 1;
                                    adp(i,:) = sscanf(tline,'%f',[1,nzen+1]);
                                end
                                satx.gps.adp{sno,fno} = adp;
                            end
                        end
                    elseif strcmp(tag,'START OF FREQUENCY') && strcmp(tline(4:6),'G02')
                        fno = 2;
                        tline = fgetl(fid); linenum = linenum + 1;
                        tag   = strtrim(tline(61:end));
                        if strcmp(tag,'NORTH / EAST / UP')
                            satx.gps.neu(sno,:,fno) = sscanf(tline,'%f',[1,3]);
                            tline = fgetl(fid); linenum = linenum + 1;
                            satx.gps.nad{sno,fno} = sscanf(tline(9:end),'%f',[1,nzen]);
                            if dazi~=0
                                nn = 360/dazi + 1;
                                adp = NaN(nn,nzen+1);
                                for i=1:nn
                                    tline = fgetl(fid);
                                    linenum = linenum + 1;
                                    adp(i,:) = sscanf(tline,'%f',[1,nzen+1]);
                                end
                                satx.gps.adp{sno,fno} = adp;
                            end
                        end
                    end
                end
            end
        else
            continue
        end
    end

catch ME
    err.cod = 2;
    msg{1} = ['Hata mesajı:',ME.message]; 
    msg{2} = ['"',ME.stack(1).name,'" fonksiyonunun ', num2str(ME.stack(1).line),'. satırında hata!'];
    err.msg = msg;
    satx = [];
    return
end

end