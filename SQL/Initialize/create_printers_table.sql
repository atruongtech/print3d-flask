use printapp_dev;
CREATE TABLE printers (
	PrinterId INT NOT NULL auto_increment,
    UserPrinterId INT,
    UserId INT,
    PrinterName nvarchar(50),
    DateAcquired Date,
    NumberOfPrints INT,
    PrintTimeHours int,
    PrinterSource nvarchar(255),
    BeltMaintInt Int,
    BeltMaintLast Int,
    WireMaintInt Int,
    WireMaintLast Int,
    LubeMaintInt Int,
    LubeMaintLast Int,
    MainPrinterImageId Int,
    foreign key(MainPrinterImageId) references images(ImageId),
    foreign key(UserId) references users(UserId),
    primary key(PrinterId)
    
);