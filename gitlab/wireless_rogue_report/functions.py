import re

ssid_pattern1=r"-HP.*"
ssid_pattern2=r"acadia.*"
ssid_pattern3=r"ADI-EA.*"
ssid_pattern4=r"ADI-HH.*"
ssid_pattern5=r"Android.*"
ssid_pattern6=r".*cruze.*"
ssid_pattern7=r"ATT"
ssid_pattern8=r"Audi.*"
ssid_pattern9=r"Camaro.*"
ssid_pattern10=r"car.*"
ssid_pattern11=r"carplay.*"
ssid_pattern12=r"CenturyLink.*"
ssid_pattern13=r".*Chevy.*"
ssid_pattern14=r"Click.*"
ssid_pattern15=r".*Colorado.*"
ssid_pattern16=r"CTNA.*"
ssid_pattern17=r"Denali.*"
ssid_pattern18=r"DIRECT.*"
ssid_pattern19=r"Fairmount.*"
ssid_pattern20=r"fmc-.*"
ssid_pattern21=r"Forestry Court.*"
ssid_pattern22=r"Freeland Spirits.*"
ssid_pattern23=r"Galaxy.*"
ssid_pattern24=r".*GMC.*"
ssid_pattern25=r"Hotspot.*"
ssid_pattern26=r"HP-.*"
ssid_pattern27=r"Huawei.*"
ssid_pattern28=r"INFINITUM.*"
ssid_pattern29=r"iPad.*"
ssid_pattern30=r"Jetpack.*"
ssid_pattern31=r"Kaiser.*"
ssid_pattern32=r"LG.*"
ssid_pattern33=r"LinkSys.*"
ssid_pattern34=r"Loves.*"
ssid_pattern35=r"Malibu.*"
ssid_pattern36=r"MetroPCS.*"
ssid_pattern37=r".*MiFi.*"
ssid_pattern38=r"Montgomery.Park.Conference.Rooms.*"
ssid_pattern39=r"Moto.*"
ssid_pattern40=r"myChevrolet.*"
ssid_pattern41=r"NETGEAR.*"
ssid_pattern42=r"Omnitracs.*"
ssid_pattern43=r"ONP_SVP.*"
ssid_pattern44=r".*Phone.*"
ssid_pattern45=r"PNet.*"
ssid_pattern46=r"QB-.*"
ssid_pattern47=r"Silverado.*"
ssid_pattern48=r"Sprint.*"
ssid_pattern49=r"T-Mobile.*"
ssid_pattern50=r"Tahoe.*"
ssid_pattern51=r"TCSD_.*"
ssid_pattern52=r"trax.*"
ssid_pattern53=r"Upshur.*"
ssid_pattern54=r"USBLink2"
ssid_pattern55=r"Verizon.*"
ssid_pattern56=r"WebMD.*"
ssid_pattern57=r"WestPAC.*"
ssid_pattern58=r"WiFi.*"
ssid_pattern59=r"Xfinity.*"
ssid_pattern60=r"Yukon.*"
ssid_pattern61=r".*Hotspot.*"
ssid_pattern62=r".*Cruze.*"
ssid_pattern63=r"CareHere.*"
ssid_pattern64=r"iPhone.*"
ssid_pattern65=r".*SpectrumWiFi.*"
ssid_pattern66=r"Subway Wifi"
ssid_pattern67=r"Third Creek Dentristy-Guest"
ssid_pattern68=r"Barrierhome"
ssid_pattern69=r"baseball14"
ssid_pattern70=r"Cleveland Ped Guest"
ssid_pattern71=r"Cleveland-Chief"
ssid_pattern72=r"ezviz_.*"
ssid_pattern73=r"Stanley.*"
ssid_pattern74=r"Airbag"
ssid_pattern75=r"Airtanks"
ssid_pattern76=r"BatteryBuildUP"
ssid_pattern77=r"FanNut"
ssid_pattern78=r"FootValve"
ssid_pattern79=r"RearAxle"
ssid_pattern80=r"RearEngine.*"
ssid_pattern81=r"Steer.*"
ssid_pattern82=r"ChsHarnFrameGnd"
ssid_pattern83=r"OrbisRPM.*"
ssid_pattern84=r"delhaize"
ssid_pattern85=r"DirectRun.*"
ssid_pattern86=r"sdp5g"
ssid_pattern87=r"CabDoorStriker"
ssid_pattern88=r"Axalta"
ssid_pattern89=r"ARLO.*"
ssid_pattern90=r"MacLellan Wifi"
ssid_pattern91=r"Crowsnest"
ssid_pattern92=r"FREIGHTLINER"
ssid_pattern93=r"MTH AUTOMATION NETWORK"
ssid_pattern94=r"AMXWAP1"
ssid_pattern95=r"Tool Crib.*"
ssid_pattern96=r"Drivers"
ssid_pattern97=r"Elevate-432F"
ssid_pattern98=r"Estridge .*"
ssid_pattern99=r"GCD-Plant5-Shop"
ssid_pattern100=r"NGC_Wireless"
ssid_pattern101=r"NGCGuest"
ssid_pattern102=r"TF-WIFI_21BAD6"
ssid_pattern103=r"UAW"
ssid_pattern104=r"Cafeteria"
ssid_pattern105=r"\*.*HIDDEN\*.*"
ssid_pattern106=r"ASUS.*"
ssid_pattern107=r"SEFLHH" #FTWCO
ssid_pattern108=r"sefl"   #FTWCO
ssid_pattern109=r"sefl2"  #FTWCO 
ssid_pattern110=r"semc"   #FTWCO
ssid_pattern111=r"WPA-Sonepar" # Vallen aka Sonepar
ssid_pattern112=r"eclipsewpa2" # Vallen aka Sonepar
ssid_pattern113=r"OrbisRPM.*" # CTMP
ssid_pattern114=r"Cleveland TMP Lobby" # CTMP
ssid_pattern115=r"LowerRadiator" # CTMP
ssid_pattern116=r"adidas_free" # PTMP
ssid_pattern117=r"adi_mobile" # PTMP
ssid_pattern118=r"moto .*"
ssid_pattern119=r"MANSIONINN" # SANT
ssid_pattern120=r"myChevrolet"
ssid_pattern121=r"Linksys.*"
ssid_pattern122=r"HMANSION" # SANT
ssid_pattern123=r"HUAWEI .*"
ssid_pattern124=r"Alcatel .*" 
ssid_pattern125=r"TP-Link.*"
ssid_pattern126=r"edenred"
ssid_pattern127=r"telcel"
ssid_pattern128=r"DaimlerAudio" # SANT
ssid_pattern129=r"finsa net" # MONT
ssid_pattern130=r"wlspolomex" # MONT
ssid_pattern131=r"Piso 2_Sala 2" # MONT
ssid_pattern132=r"Piso 2 sala 4" # MONT
ssid_pattern133=r"Sala_RH" # MONT
ssid_pattern134=r"Piso 2_Sala 1" # MONT
ssid_pattern135=r"Piso 2_Sala 4" # MONT


classification1="WiFi Direct (Printer)"
classification2="Mobile Hotspot"
classification3="Neighboring Business/Resident"
classification4="Hotspot"
classification5="ClickShare"
classification6="WiFi Direct (Laptop)"
classification7="WiFi Direct"
classification8="Possible Vendors"
classification9="Nexiq WVL2"
classification10="Guest Wifi"
classification11="Security Camera"
classification12="Torque Controller"
classification13="Offline Bendix"
classification14="Vendor"
classification15="Automation"
classification16="Torque Tool"
classification17="SSID Is Not Broadcast"
classification18="Speakers"


def classify_rogue(ssid):
    if re.match(ssid_pattern1, ssid):
        classification = classification1
    elif re.match(ssid_pattern2, ssid):
        classification = classification2
    elif re.match(ssid_pattern3, ssid):
        classification = classification3
    elif re.match(ssid_pattern4, ssid):
        classification = classification3
    elif re.match(ssid_pattern5, ssid):
        classification = classification2
    elif re.match(ssid_pattern6, ssid):
        classification = classification2
    elif re.match(ssid_pattern7, ssid):
        classification = classification4
    elif re.match(ssid_pattern8, ssid):
        classification = classification2
    elif re.match(ssid_pattern9, ssid):
        classification = classification2
    elif re.match(ssid_pattern10, ssid):
        classification = classification2
    elif re.match(ssid_pattern11, ssid):
        classification = classification2
    elif re.match(ssid_pattern12, ssid):
        classification = classification4
    elif re.match(ssid_pattern13, ssid):
        classification = classification2
    elif re.match(ssid_pattern14, ssid):
        classification = classification5
    elif re.match(ssid_pattern15, ssid):
        classification = classification2
    elif re.match(ssid_pattern16, ssid):
        classification = classification6
    elif re.match(ssid_pattern17, ssid):
        classification = classification2
    elif re.match(ssid_pattern18, ssid):
        classification = classification7
    elif re.match(ssid_pattern19, ssid):
        classification = classification3
    elif re.match(ssid_pattern20, ssid):
        classification = classification3
    elif re.match(ssid_pattern21, ssid):
        classification = classification3
    elif re.match(ssid_pattern22, ssid):
        classification = classification3
    elif re.match(ssid_pattern23, ssid):
        classification = classification2
    elif re.match(ssid_pattern24, ssid):
        classification = classification2
    elif re.match(ssid_pattern25, ssid):
        classification = classification4
    elif re.match(ssid_pattern26, ssid):
        classification = classification1
    elif re.match(ssid_pattern27, ssid):
        classification = classification2
    elif re.match(ssid_pattern28, ssid):
        classification = classification8
    elif re.match(ssid_pattern29, ssid):
        classification = classification2
    elif re.match(ssid_pattern30, ssid):
        classification = classification4
    elif re.match(ssid_pattern31, ssid):
        classification = classification3
    elif re.match(ssid_pattern32, ssid):
        classification = classification2
    elif re.match(ssid_pattern33, ssid):
        classification = classification4
    elif re.match(ssid_pattern34, ssid):
        classification = classification3
    elif re.match(ssid_pattern35, ssid):
        classification = classification2
    elif re.match(ssid_pattern36, ssid):
        classification = classification4
    elif re.match(ssid_pattern37, ssid):
        classification = classification4
    elif re.match(ssid_pattern38, ssid):
        classification = classification3
    elif re.match(ssid_pattern39, ssid):
        classification = classification2
    elif re.match(ssid_pattern40, ssid):
        classification = classification2
    elif re.match(ssid_pattern41, ssid):
        classification = classification3
    elif re.match(ssid_pattern42, ssid):
        classification = classification8
    elif re.match(ssid_pattern43, ssid):
        classification = classification3
    elif re.match(ssid_pattern44, ssid):
        classification = classification2
    elif re.match(ssid_pattern45, ssid):
        classification = classification16
    elif re.match(ssid_pattern46, ssid):
        classification = classification16
    elif re.match(ssid_pattern47, ssid):
        classification = classification2
    elif re.match(ssid_pattern48, ssid):
        classification = classification2
    elif re.match(ssid_pattern49, ssid):
        classification = classification4
    elif re.match(ssid_pattern50, ssid):
        classification = classification2
    elif re.match(ssid_pattern51, ssid):
        classification = classification3
    elif re.match(ssid_pattern52, ssid):
        classification = classification2
    elif re.match(ssid_pattern53, ssid):
        classification = classification3
    elif re.match(ssid_pattern54, ssid):
        classification = classification9
    elif re.match(ssid_pattern55, ssid):
        classification = classification4
    elif re.match(ssid_pattern56, ssid):
        classification = classification3
    elif re.match(ssid_pattern57, ssid):
        classification = classification3
    elif re.match(ssid_pattern58, ssid):
        classification = classification4
    elif re.match(ssid_pattern59, ssid):
        classification = classification4
    elif re.match(ssid_pattern60, ssid):
        classification = classification2
    elif re.match(ssid_pattern61, ssid):
        classification = classification4
    elif re.match(ssid_pattern62, ssid):
        classification = classification2
    elif re.match(ssid_pattern63, ssid):
        classification = classification14
    elif re.match(ssid_pattern64, ssid):
        classification = classification2
    elif re.match(ssid_pattern65, ssid):
        classification = classification10
    elif re.match(ssid_pattern66, ssid):
        classification = classification3
    elif re.match(ssid_pattern67, ssid):
        classification = classification3
    elif re.match(ssid_pattern68, ssid):
        classification = classification3
    elif re.match(ssid_pattern69, ssid):
        classification = classification3
    elif re.match(ssid_pattern70, ssid):
        classification = classification3
    elif re.match(ssid_pattern71, ssid):
        classification = classification3
    elif re.match(ssid_pattern72, ssid):
        classification = classification11
    elif re.match(ssid_pattern73, ssid):
        classification = classification12
    elif re.match(ssid_pattern74, ssid):
        classification = classification12
    elif re.match(ssid_pattern75, ssid):
        classification = classification12
    elif re.match(ssid_pattern76, ssid):
        classification = classification12
    elif re.match(ssid_pattern77, ssid):
        classification = classification12
    elif re.match(ssid_pattern78, ssid):
        classification = classification12
    elif re.match(ssid_pattern79, ssid):
        classification = classification12
    elif re.match(ssid_pattern80, ssid):
        classification = classification12
    elif re.match(ssid_pattern81, ssid):
        classification = classification12
    elif re.match(ssid_pattern82, ssid):
        classification = classification12
    elif re.match(ssid_pattern83, ssid):
        classification = classification8
    elif re.match(ssid_pattern84, ssid):
        classification = classification3
    elif re.match(ssid_pattern85, ssid):
        classification = classification10
    elif re.match(ssid_pattern86, ssid):
        classification = classification13
    elif re.match(ssid_pattern87, ssid):
        classification = classification12
    elif re.match(ssid_pattern88, ssid):
        classification = classification14
    elif re.match(ssid_pattern89, ssid):
        classification = classification3
    elif re.match(ssid_pattern90, ssid):
        classification = classification14
    elif re.match(ssid_pattern91, ssid):
        classification = classification14
    elif re.match(ssid_pattern92, ssid):
        classification = classification10
    elif re.match(ssid_pattern93, ssid):
        classification = classification15
    elif re.match(ssid_pattern94, ssid):
        classification = classification15
    elif re.match(ssid_pattern95, ssid):
        classification = classification14
    elif re.match(ssid_pattern96, ssid):
        classification = classification3
    elif re.match(ssid_pattern97, ssid):
        classification = classification3
    elif re.match(ssid_pattern98, ssid):
        classification = classification3
    elif re.match(ssid_pattern99, ssid):
        classification = classification3
    elif re.match(ssid_pattern100, ssid):
        classification = classification3
    elif re.match(ssid_pattern101, ssid):
        classification = classification3
    elif re.match(ssid_pattern102, ssid):
        classification = classification3
    elif re.match(ssid_pattern103, ssid):
        classification = classification14
    elif re.match(ssid_pattern104, ssid):
        classification = classification10
    elif re.match(ssid_pattern105, ssid):
        classification = classification17
    elif re.match(ssid_pattern106, ssid):
        classification = classification3
    elif re.match(ssid_pattern107, ssid):
        classification = classification3
    elif re.match(ssid_pattern108, ssid):
        classification = classification3
    elif re.match(ssid_pattern109, ssid):
        classification = classification3
    elif re.match(ssid_pattern110, ssid):
        classification = classification3
    elif re.match(ssid_pattern111, ssid):
        classification = classification14
    elif re.match(ssid_pattern112, ssid):
        classification = classification14
    elif re.match(ssid_pattern113, ssid):
        classification = classification14
    elif re.match(ssid_pattern114, ssid):
        classification = classification10
    elif re.match(ssid_pattern115, ssid):
        classification = classification12
    elif re.match(ssid_pattern116, ssid):
        classification = classification3
    elif re.match(ssid_pattern117, ssid):
        classification = classification3
    elif re.match(ssid_pattern118, ssid):
        classification = classification2
    elif re.match(ssid_pattern119, ssid):
        classification = classification3
    elif re.match(ssid_pattern120, ssid):
        classification = classification2
    elif re.match(ssid_pattern121, ssid):
        classification = classification4
    elif re.match(ssid_pattern122, ssid):
        classification = classification3
    elif re.match(ssid_pattern123, ssid):
        classification = classification2
    elif re.match(ssid_pattern124, ssid):
        classification = classification2
    elif re.match(ssid_pattern125, ssid):
        classification = classification4
    elif re.match(ssid_pattern126, ssid):
        classification = classification2
    elif re.match(ssid_pattern127, ssid):
        classification = classification2
    elif re.match(ssid_pattern128, ssid):
        classification = classification18
    elif re.match(ssid_pattern129, ssid):
        classification = classification14
    elif re.match(ssid_pattern130, ssid):
        classification = classification14
    elif re.match(ssid_pattern131, ssid):
        classification = classification5
    elif re.match(ssid_pattern132, ssid):
        classification = classification5
    elif re.match(ssid_pattern133, ssid):
        classification = classification5
    elif re.match(ssid_pattern134, ssid):
        classification = classification5
    elif re.match(ssid_pattern135, ssid):
        classification = classification5

    else:
        classification = "Interfering Transmitter"
    return classification

def site_email(wlc):
    if wlc=='WLCNAME1':
        email='email1@emailaddr.com, email2@emailaddr.com'
    elif wlc=='WLCNAME2':
        email='email3@emailaddr.com, email4@emailaddr.com'
    else: 
        email='Unknown'
    return email

