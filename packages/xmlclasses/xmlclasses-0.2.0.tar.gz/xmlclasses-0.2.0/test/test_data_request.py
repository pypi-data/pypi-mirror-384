test_data = """<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
<PutDataRequest RequestId="802b3a9a-aa15-47dc-951d-7cba421c940d" MessageTime="2025-02-24T14:17:06.903+00:00"
    TransmissionComplete="true" TransmissionSuspended="false">
    <Positions EventTime="2022-05-16T17:13:10.800+02:00">
        <MetaData MatchId="MLS-MAT-0002WQ" Type="pitch-size">
            <PitchSize X="100.00" Y="68.00" />
        </MetaData>
        <FrameSet GameSection="firstHalf" MatchId="MLS-MAT-0002WQ" TeamId="MLS-CLU-00000G" PersonId="MLS-OBJ-0000IQ">
            <Frame N="10002" T="2022-05-16T15:30:40.920+02:00" X="7.38" Y="-6.34" S="0.00" M="1" A="0.00" D="0.00" />
            <Frame N="10003" T="2022-05-16T15:30:40.960+02:00" X="7.38" Y="-6.35" S="0.18" M="1" A="6.11" D="8.32" />
            <Frame N="10004" T="2022-05-16T15:30:41.000+02:00" X="7.39" Y="-6.36" S="0.44" M="1" A="6.25" D="10.00" />
        </FrameSet>
        <FrameSet GameSection="secondHalf" MatchId="MLS-MAT-0002WQ" TeamId="MLS-CLU-00000G" PersonId="MLS-OBJ-0000IQ">
            <Frame N="10002" T="2022-05-16T15:30:40.920+02:00" X="7.38" Y="-6.34" S="0.00" M="46" A="0.00" D="0.00" />
            <Frame N="10003" T="2022-05-16T15:30:40.960+02:00" X="7.38" Y="-6.35" S="0.18" M="46" A="6.11" D="8.32" />
            <Frame N="10004" T="2022-05-16T15:30:41.000+02:00" X="7.39" Y="-6.36" S="0.44" M="46" A="6.25" D="10.00" />
        </FrameSet>
    </Positions>
</PutDataRequest>"""


xml_country = """
<?xml version="1.0"?>
<data>
    <country name="Liechtenstein">
        <rank>1</rank>
        <year>2008</year>
        <gdppc>141100</gdppc>
        <neighbor name="Austria" direction="E"/>
        <neighbor name="Switzerland" direction="W"/>
    </country>
    <country name="Singapore">
        <rank>4</rank>
        <year>2011</year>
        <gdppc>59900</gdppc>
        <neighbor name="Malaysia" direction="N"/>
    </country>
    <country name="Panama">
        <rank>68</rank>
        <year>2011</year>
        <gdppc>13600</gdppc>
        <neighbor name="Costa Rica" direction="W"/>
        <neighbor name="Colombia" direction="E"/>
    </country>
</data>
"""
