#!/usr/bin/env python
#
# Copyright 2011 Yummy Melon Software LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import sys
import subprocess
import getopt
import glob
import shutil

helpString = """

DESCRIPTION
 enscript2dropbox is a utility which generates colorized HTML or pdf output of
 a programming source file and places it into Dropbox for viewing in lieu
 of printing out the source file. By default, output generated will be placed
 in the directory $HOME/Dropbox/Documents/printouts

 Implementation-wise, enscript2dropbox is a Python wrapper around the enscript
 and pstopdf (OS X) or ps2pdf (Linux) utilities. You must also have Dropbox
 installed and configured on your system.

  -h, --help                   print help
  -E[lang], --highlight[=lang] Highlight using enscript --highlight option
  -w[lang], --language[=lang]  Set output file format. Supported formats are html (default) and pdf.

EXAMPLE
  $ enscript2dropbox foo.[mh]

SEE ALSO
enscript(1), pstopdf(1) [OS X], ps2pdf(1) [Linux]
"""

usageString = "enscript2dropbox [options] file1 file2 ..."

class Enscript2Dropbox:
    version = '0.1'
    extensionMap = { '.m' : 'objc',
                     '.h' : 'objc' }

    def __init__(self):
        self.cmdList = None
        self.outfileName = None
        self.dropboxPath = os.path.join(os.environ['HOME'], 'Dropbox', 'Documents', 'printouts')
        if (not os.path.exists(self.dropboxPath)):
            os.makedirs(self.dropboxPath)
            
            
    def genBaseCommand(self):
        self.cmdList = []
        self.cmdList.append('enscript')
        self.cmdList.append('-1RG')
        self.cmdList.append('-T4')
        self.cmdList.append('-fCourier7')
        self.cmdList.append('--color')

    def genHighlightCommand(self, highlight, suffix):
        result = []
        if highlight:
            result.append('--highlight=%s' % highlight)
        
        elif self.extensionMap.has_key(suffix):
            highlight = self.extensionMap[suffix]
            result.append('--highlight=%s' % highlight)
        else:
            result.append('-E')

        return result

    def genLanguageCommand(self, language, fileName):
        result = []
        
        
        if language == 'html':
            result.append('--language=html')
            self.outfileName = '%s.html' % fileName
        elif language == 'pdf':
            result.append('--language=PostScript')
            self.outfileName = '%s.ps' % fileName

        result.append('-o')
        result.append(os.path.join(self.getTempDir(), self.outfileName))
        return result

    def getTempDir(self):
        result = None
        if os.environ.has_key('TMPDIR'):
            result = os.environ['TMPDIR']
        elif os.environ.has_key('TMP'):
            result = os.environ['TMP']
        elif os.environ.has_key('TEMP'):
            result = os.environ['TEMP']
        else:
            result = '/tmp'
                
        return result


    def installInDropbox(self):
        targetPath = os.path.join(self.dropboxPath, self.outfileName)
                
        if os.path.exists(targetPath):
            #sys.stderr.write('writing over older copy of %s\n' % pdfFileName)
            os.unlink(targetPath)

        shutil.move(os.path.join(self.getTempDir(), self.outfileName),
                    targetPath)

        
    def genPdf(self):
        print 'generating pdf'
        tempFilePath = os.path.join(self.getTempDir(), self.outfileName) 
        pdfCmd = []

        if sys.platform in ('darwin',):
            pdfCmd.append('pstopdf')
        else:
            pdfCmd.append('ps2pdf')

        pdfCmd.append(tempFilePath)
        print ' '.join(pdfCmd)
        subprocess.call(pdfCmd)
        
        prefix, suffix = os.path.splitext(self.outfileName)
        self.outfileName = prefix + '.pdf'
        os.unlink(tempFilePath)

        if sys.platform not in ('darwin',):
            shutil.move(self.outfileName, self.getTempDir())
        
        
    def run(self, optlist, args):
        highlight = None
        language = 'html'
        
        self.genBaseCommand()
        for o, i in optlist:
            if o in ('-h', '--help'):
                sys.stderr.write(usageString)
                sys.stderr.write(helpString)
                sys.exit(0)

            elif o in ('-E', '--highlight'):
                highlight = i

            elif o in ('-w', '-W', '--language'):
                language = i

            elif o in ('-v', '--version'):
                sys.stderr.write('%s\n' % self.version)
                sys.exit(0)
                


        if len(args) == 0:
            sys.stderr.write('ERROR: You must specify a filename.\n')
            sys.exit(1)
                

        for arg in args:
            for fileName in glob.iglob(arg):
                #print fileName
                prefix, suffix = os.path.splitext(fileName)
                highlightCommand = self.genHighlightCommand(highlight, suffix)

                languageCommand = self.genLanguageCommand(language, fileName)

                commandList = self.cmdList + highlightCommand + languageCommand
                commandList.append(fileName)
                
                print ' '.join(commandList)
                subprocess.call(commandList)

                if language == 'pdf':
                    self.genPdf()
                    
                self.installInDropbox()


if __name__ == '__main__':
    try:
        optlist, args = getopt.getopt(sys.argv[1:],
                                      'vhE:w:W:',
                                      ['version', 'help', 'highlight=', 'language='])
                                       
    except getopt.error, msg:
        sys.stderr.write(msg.msg + '\n')
        sys.stderr.write(usageString)
        sys.exit(1)

    highlight = False


    app = Enscript2Dropbox()
    app.run(optlist, args)
    
