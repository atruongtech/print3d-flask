delete from prints where PrintId <> -1;
delete from filaments where FilamentId <> -1;
delete from colorfamilies where ColorFamilyId <> -1;
delete from printers where PrinterId <> -1;
delete from images where ImageId <> -1;
delete from users where UserId <> -1;

insert into colorfamilies (ColorFamilyName) 
values ('Red'),('Orange'),('Yellow'),('Green'),('Blue'),('Purple'), ('White'),('Black');

insert into users (UserName)
values ('Alan'),('John'),('Lee'),('Bonnie'),('Roger');

insert into printers (UserId, 
						UserPrinterId, 
                        PrinterName, 
                        DateAcquired, 
                        NumberOfPrints, 
                        PrintTimeHours, 
                        PrinterSource, 
                        BeltMaintInt, 
                        BeltMaintLast,
                        WireMaintInt,
                        WireMaintLast,
                        LubeMaintInt,
                        LubeMaintLast)
values (1,1,'Maker Select', Date('2017-4-01'), 5, 20, 'Newegg', 100, 0, 100, 0, 100, 0),
		(1,2,'LulzBot Mini', Date('2017-4-01'), 10, 20, 'Amazon', 100, 0, 100, 0, 100, 0),
        (2,1,'Wanhao D7', Date('2017-4-03'), 5, 100, 'Wanhao', 100, 0, 100, 0, 100, 0);
        
        
insert into filaments (UserId,
						UserFilamentId,
                        Material,
                        Brand,
                        ColorFamilyId,
                        HtmlColor,
                        LengthRemain,
                        DateAcquired,
                        FilamentSource)
values (1,1,'PLA','Monoprice', 1, '#f47442', 50, DATE('2016-02-01'), 'Monoprice'),
		(1,2,'PETG','Inland', 8, '#000000', 50, DATE('2016-02-01'), 'Microcenter'),
        (2,1,'PETG','Inland', 8, '#000000', 50, DATE('2016-02-01'), 'Microcenter');
        
        
insert into prints (UserId,
					PrintName,
                    SourceUrl,
                    Success,
                    PrintTimeHours,
                    PrintTimeMinutes,
                    FilamentId,
                    PrinterId,
                    PrintDate,
                    ModelFileUrl,
                    LengthUsed)
values (1, '3D Benchy', 'http://www.thingiverse.com/thing:763622', 1, 4,32,1,1,DATE('2017-3-1'), NULL, 4), 
		(1, 'Ninja Stars', 'http://www.thingiverse.com/thing:763622', 1, 4,32,1,1,DATE('2017-3-1'), NULL, 4),
        (2, '3D Benchy', 'http://www.thingiverse.com/thing:763622', 1, 4,32,3,3,DATE('2017-3-1'), NULL, 4)
