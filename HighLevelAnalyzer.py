# High Level Analyzer
# For more information and documentation, please go to https://support.saleae.com/extensions/high-level-analyzer-extensions

from saleae.analyzers import HighLevelAnalyzer, AnalyzerFrame, StringSetting, NumberSetting, ChoicesSetting


# High level analyzers must subclass the HighLevelAnalyzer class.
class Hla(HighLevelAnalyzer):

    output_format = ChoicesSetting(choices=('Decimal', 'Hexadecimal'))
    # An optional list of types this analyzer produces, providing a way to customize the way frames are displayed in Logic 2.
    result_types = {
        'mytype': {
            'format': '{{data.result}}'
        }
    }

    def __init__(self):
        '''
        Initialize HLA.

        Settings can be accessed using the same name used above.
        '''
        #A byte we will be building up bit by bit.
        self.byte_buildup = []
        self.buildup_start_time = None
        #This will initialize the first byte of the capture so the times can be relative to the capture frame
        self.first_frame_start = None
    def decode(self, frame: AnalyzerFrame):
        '''
        Process a frame from the input analyzer, and optionally return a single `AnalyzerFrame` or a list of `AnalyzerFrame`s.

        The type and data values in `frame` will depend on the input analyzer.
        '''
        if self.first_frame_start is None:
            self.first_frame_start = frame.start_time
        this_frame_size = int(float(frame.end_time - frame.start_time) * 10e3)
        frame_label = ""
        if 133<this_frame_size<137:
            frame_label = "START FRAME"
        #If nothing is happening then ignore everything and wipe it out
        elif this_frame_size > 150:
            self.byte_buildup = []
            self.buildup_start_time = None
            return
        elif 111<this_frame_size<115:
            frame_label = "REPEAT"
            self.byte_buildup = []
            self.buildup_start_time = None
        elif this_frame_size < 8: #Captures the end of a repeat
            return
        else:
            print("frame processing")
            print(float(frame.start_time - self.first_frame_start)*1e3)
            print(this_frame_size)
            interpreted_bit = 9999
            #This must be a normal bit, build up the byte.
            if self.buildup_start_time is None:
                self.buildup_start_time = frame.start_time
            if 9<this_frame_size<13:
                interpreted_bit = 0
            if 20<this_frame_size<24:
                interpreted_bit = 1
            self.byte_buildup.append(interpreted_bit)
            if len(self.byte_buildup) == 8:
                print(self.byte_buildup)
                #Reverse it: LSB first.
                self.byte_buildup = reversed(self.byte_buildup)
                #byte is built, flush it
                byte_value = 0
                for i in self.byte_buildup:
                    byte_value *= 2
                    byte_value += i
                framestart = self.buildup_start_time
                self.byte_buildup = []
                self.buildup_start_time = None
                if self.output_format == 'Decimal':
                    out_string = str(byte_value)
                elif self.output_format == 'Hexadecimal':
                    out_string = f"0x{byte_value:02X}"
                return AnalyzerFrame('mytype', framestart, frame.end_time, {
                    'result': out_string
                })
            else:
                return
        # Return the data frame itself
        return AnalyzerFrame('mytype', frame.start_time, frame.end_time, {
            'result': frame_label
        })
