@testing_solution
@ais
Feature: Test decode of NMEA AIS raw to dict

    @nmea_to_dict_without_tagblock
    Scenario: from NMEA raw to dict (without tagblock)
        Given RAW = '!AIVDM,1,1,,A,13KG`rU0001RbwdT6CR3TB3f0000,0*4E'
        
        When MSG_DICT = decode NMEA AIS raw RAW as dictionary
        
        Then MSG_TABLE = convert dictionary MSG_DICT to name/value table
        Then table MSG_TABLE is
            | Name       | Value     |
            | 'accuracy' | False     |
            | 'course'   | 91.3      |
            | 'heading'  | 65        |
            | 'lat'      | 63.086733 |
            | 'lon'      | 21.555183 |
            | 'maneuver' | 0         |
            | 'mmsi'     | 230025450 |
            | 'msg_type' | 1         |
            | 'radio'    | 0         |
            | 'raim'     | False     |
            | 'repeat'   | 0         |
            | 'second'   | 55        |
            | 'speed'    | 0.0       |
            | 'status'   | 5         |
            | 'turn'     | 0.0       |


    @nmea_to_dict_with_tagblock
    @without_merge
    Scenario: from NMEA raw to dict (with tagblock, without merge)
        Given RAW = '\\s:STATION1,t:Hello*2\\!AIVDM,1,1,,A,13KG`rU0001RbwdT6CR3TB3f0000,0*4E'
        
        When TB_DICT, MSG_DICT = decode NMEA AIS raw RAW as dictionary
        
        Then TB_TABLE = convert dictionary TB_DICT to name/value table
        Then table TB_TABLE is
            | Name             | Value      |
            | 'source_station' | 'STATION1' |
            | 'text'           | 'Hello'    |
        
        Then MSG_TABLE = convert dictionary MSG_DICT to name/value table
        Then table MSG_TABLE is
            | Name       | Value     |
            | 'accuracy' | False     |
            | 'course'   | 91.3      |
            | 'heading'  | 65        |
            | 'lat'      | 63.086733 |
            | 'lon'      | 21.555183 |
            | 'maneuver' | 0         |
            | 'mmsi'     | 230025450 |
            | 'msg_type' | 1         |
            | 'radio'    | 0         |
            | 'raim'     | False     |
            | 'repeat'   | 0         |
            | 'second'   | 55        |
            | 'speed'    | 0.0       |
            | 'status'   | 5         |
            | 'turn'     | 0.0       |


    @nmea_to_dict_with_tagblock
    @with_merge
    Scenario: from NMEA raw to dict (with tagblock, with merge)
        Given RAW = '\\s:STATION1,t:Hello*2\\!AIVDM,1,1,,A,13KG`rU0001RbwdT6CR3TB3f0000,0*4E'
        
        When MSG_DICT = decode NMEA AIS raw RAW as dictionary (merge tag block and message dictionaries)
        
        Then MSG_TABLE = convert dictionary MSG_DICT to name/value table
        Then table MSG_TABLE is
            | Name             | Value      |
            | 'accuracy'       | False      |
            | 'course'         | 91.3       |
            | 'heading'        | 65         |
            | 'lat'            | 63.086733  |
            | 'lon'            | 21.555183  |
            | 'maneuver'       | 0          |
            | 'mmsi'           | 230025450  |
            | 'msg_type'       | 1          |
            | 'radio'          | 0          |
            | 'raim'           | False      |
            | 'repeat'         | 0          |
            | 'second'         | 55         |
            | 'source_station' | 'STATION1' |
            | 'speed'          | 0.0        |
            | 'status'         | 5          |
            | 'text'           | 'Hello'    |
            | 'turn'           | 0.0        |



