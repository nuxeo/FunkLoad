import pkg_resources, re
ENTRYPOINT = 'funkload.plugins.monitor'

gd_colors=[['red', 0xff0000],
           ['green', 0x00ff00],
           ['blue', 0x0000ff],
           ['yellow', 0xffff00],
           ['purple', 0x7f007f],
          ] 

class MonitorPlugins():
    MONITORS = {}
    def __init__(self, conf=None):
        self.conf = conf

    def registerPlugins(self):
        for entrypoint in pkg_resources.iter_entry_points(ENTRYPOINT):
            p=entrypoint.load()(self.conf)
            self.MONITORS[p.name]=p

class MonitorPlugin(object):
    name = None
    title=""
    unit = ""
    ylabel=""
    plots={}

    def __init__(self, conf=None):
        if self.name == None:
            self.name=self.__class__.__name__
        self._conf = conf

    def _checkKernelRev(self):
        """Check the linux kernel revision."""
        version = open("/proc/version").readline()
        kernel_rev = float(re.search(r'version (\d+\.\d+)\.\d+',
                                     version).group(1))
        if (kernel_rev > 2.6) or (kernel_rev < 2.4):
            sys.stderr.write(
                "Sorry, kernel v%0.1f is not supported\n" % kernel_rev)
            sys.exit(-1)
        return kernel_rev

    def gnuplot(self, times, host, image_path, data_path, gplot_path, chart_size, stats):
        parsed=self.parseStats(stats)
        if parsed==None:
            return None

        lines=[]

        lines.append('set output "%s"' % image_path)
        lines.append('set terminal png size %d,%d' % chart_size)
        lines.append('set grid back')
        lines.append('set xdata time')
        lines.append('set timefmt "%H:%M:%S"')
        lines.append('set format x "%H:%M"')

        ylabel = self.ylabel
        if self.unit!="":
            ylabel+='[%s]' % self.unit
        lines.append('set title "%s"' % self.title)
        lines.append('set ylabel "%s"' % ylabel)
        plot = 'plot "%s"' % data_path

        li=[]
        data = [times]
        labels = ["TIME"]
        for p in self.plots.keys():
            data.append(parsed[self.plots[p][1]])
            labels.append(self.plots[p][1])
            li.append(' u 1:%d title "%s" with %s' % (len(data), p, self.plots[p][0]))
        lines.append(plot+', ""'.join(li))

        data = zip(*data)
        f = open(data_path, 'w')
        f.write("%s\n" % " ".join(labels))
        for line in data:
            f.write(' '.join([str(item) for item in line]) + '\n')
        f.close()

        f = open(gplot_path, 'w')
        f.write('\n'.join(lines) + '\n')
        f.close()

        return (self.title, image_path)

    def gdchart(self, x, times, host, image_path, stats):
        parsed=self.parseStats(stats)
        if parsed==None:
            return None

        title="%s:"%host
        data=[]
        title_parts=[]
        i=0
        for p in self.plots.keys():
            data.append(parsed[self.plots[p][1]])
            title_parts.append(" %s (%s)"%(p, gd_colors[i][0]))
            i+=1
        title+=", ".join(title_parts)

        colors=[]
        for c in gd_colors:
            colors.append(c[1])

        x.title = title
        x.ytitle = self.ylabel
        x.ylabel_fmt = '%%.2f %s' % self.unit
        x.set_color = tuple(colors)
        x.title = title
        x.xtitle = 'time and CUs'
        x.setLabels(times)
        x.setData(*data)
        x.draw(image_path)

        return self.title

    def getStat(self):
        """ Read stats from system """
        pass
  
    def parseStats(self, stats):
        """ Parse MonitorInfo object list """
        pass
