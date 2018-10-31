# -*- coding: utf-8 -*-
#
#    ICRAR - International Centre for Radio Astronomy Research
#    (c) UWA - The University of Western Australia
#    Copyright by UWA (in the framework of the ICRAR)
#    All rights reserved
#
#    This library is free software; you can redistribute it and/or
#    modify it under the terms of the GNU Lesser General Public
#    License as published by the Free Software Foundation; either
#    version 2.1 of the License, or (at your option) any later version.
#
#    This library is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#    Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public
#    License along with this library; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston,
#    MA 02111-1307  USA
#

import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from jobs import JobQueue


class AutoEncoderTest(object):
    def __init__(self, directory, out, real):
        self.directory = directory
        self.out = out
        self.real = real

    def __call__(self, *args, **kwargs):
        for i in range(min(5, self.out.shape[0])):
            Visualiser.plot_output(self.directory, self.out[i], "Generator Output {0}".format(i))
            Visualiser.plot_output(self.directory, self.real[i], "Real Output {0}".format(i))
            Visualiser.plot_output(self.directory, [self.real[i], self.out[i]], "Output Real Comparison {0}".format(i))


class GANTest(object):
    def __init__(self, directory, gen_out, real_out, discriminator_out, discriminator_real):
        self.directory = directory
        self.gen_out = gen_out
        self.real_out = real_out
        self.discriminator_out = discriminator_out
        self.discriminator_real = discriminator_real

    def __call__(self, *args, **kwargs):
        for i in range(min(10, self.gen_out.shape[0])):
            Visualiser.plot_output(self.directory, self.gen_out[i], "Generator Output {0}".format(i))

        for i in range(min(10, self.real_out.shape[0])):
            Visualiser.plot_output(self.directory, self.real_out[i], "Real Data {0}".format(i))

        with open(os.path.join(self.directory, 'discriminator.txt'), 'w') as f:
            f.write("Fake Expected (Data that came from the generator): [0, 1]\n")
            for i in range(self.discriminator_out.shape[0]):
                f.write("Fake: [{:.2f}, {:.2f}]\n".format(self.discriminator_out[i][0], self.discriminator_out[i][1]))

            f.write("\nReal Expected (Data that came from the dataset): [1, 0]\n")

            for i in range(self.discriminator_real.shape[0]):
                f.write("Real: [{:.2f}, {:.2f}]\n".format(self.discriminator_real[i][0], self.discriminator_real[i][1]))


class PlotLearning(object):
    def __init__(self, directory, d_loss_real, d_loss_fake, g_loss):
        self.directory = directory
        self.d_loss_real = d_loss_real
        self.d_loss_fake = d_loss_fake
        self.g_loss = g_loss

    def __call__(self, *args, **kwargs):
        if len(self.d_loss_real) > 0:
            Visualiser.plot_learning(self.directory, self.d_loss_real, "Discriminator Loss Real")
        if len(self.d_loss_fake) > 0:
            Visualiser.plot_learning(self.directory, self.d_loss_fake, "Discriminator Loss Fake")
        if len(self.g_loss) > 0:
            Visualiser.plot_learning(self.directory, self.g_loss, "Generator Loss")


class Visualiser(object):
    def __init__(self, base_directory):
        self.d_loss_real = []
        self.d_loss_fake = []
        self.g_loss = []
        self.base_directory = base_directory

        self.queue = JobQueue(num_processes=1)

    def __del__(self):
        print("Waiting for jobs to finish...")
        self.queue.join()

    @staticmethod
    def plot_learning(directory, data, title):
        fig = plt.figure(figsize=(16, 9), dpi=80)
        plt.title(title)
        plt.xlabel('Step')
        plt.ylabel('Loss')
        plt.plot(data)
        plt.savefig(os.path.join(directory, title))
        fig.clear()
        plt.close(fig)

    @staticmethod
    def plot_output(directory, data, title):
        fig = plt.figure(figsize=(16, 9), dpi=80)
        plt.title(title)
        plt.xlabel('Sample')
        plt.ylabel('Voltage')
        if type(data) == list:
            for d in data:
                plt.plot(d)
        else:
            plt.plot(data)
        plt.savefig(os.path.join(directory, title))
        fig.clear()
        plt.close(fig)
        pass

    def _get_directory(self, epoch):
        directory = os.path.join(self.base_directory, "{0}".format(epoch))
        os.makedirs(directory, exist_ok=True)
        return directory

    def step(self, d_loss_real, d_loss_fake, g_loss):
        self.d_loss_real.append(d_loss_real)
        self.d_loss_fake.append(d_loss_fake)
        self.g_loss.append(g_loss)

    def step_autoencoder(self, loss):
        self.g_loss.append(loss)

    def test(self, epoch, discriminator, generator, noise, real):
        generator.eval()
        discriminator.eval()
        out = generator(noise)
        self.queue.submit(GANTest(directory=self._get_directory(epoch),
                                  gen_out=out.cpu().data.numpy(),
                                  real_out=real.cpu().data.numpy(),
                                  discriminator_out=discriminator(out).cpu().data.numpy(),
                                  discriminator_real=discriminator(real).cput().data.numpy()))
        generator.train()
        discriminator.train()

    def test_autoencoder(self, epoch, generator, real):
        generator.eval()
        self.queue.submit(AutoEncoderTest(directory=self._get_directory(epoch),
                                          out=generator(real).cpu().data.numpy(),
                                          real=real.cpu().data.numpy()))
        generator.train()

    def plot_training(self, epoch):
        self.queue.submit(PlotLearning(directory=self._get_directory(epoch),
                                       d_loss_real=self.d_loss_real,
                                       d_loss_fake=self.d_loss_fake,
                                       g_loss=self.g_loss))
